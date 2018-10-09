# -*- coding: utf-8 -*-
import os

from flask import request
from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse
from werkzeug.utils import secure_filename

from colleague.acl import login_required, refresh_token_required
from colleague.config import settings
from colleague.extensions import redis_conn
from colleague.models.endorsement import Endorsement
from colleague.models.user import User
from colleague.service import user_service, work_service
from colleague.utils import (ErrorCode, VerificationCode, md5,
                             st_raise_error, decode_id)
from . import compose_response


class Register(Resource):
    def __init__(self):
        self.reqparser = reqparse.RequestParser()
        self.reqparser.add_argument('device-id', type=str, location='headers', required=True)
        self.reqparser.add_argument('mobile', type=str, location='json', required=True)
        self.reqparser.add_argument('password', type=str, location='json', required=True)
        self.reqparser.add_argument('verification_code', type=str, location='json', required=True)

    def post(self):
        args = self.reqparser.parse_args()

        mobile = args["mobile"]
        password = args["password"]

        user = User.find_by_mobile(mobile)
        if user:
            raise st_raise_error(ErrorCode.ALREADY_EXIST_MOBILE)

        verification_code = redis_conn.get("verification_code:{}".format(mobile))
        if verification_code is None:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_EXPIRE)
        if verification_code != args["verification_code"]:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_NOT_MATCH)

        user = User.add_user(mobile, password)
        Endorsement.add_new_one(user.id)
        token = user.login_on(args["device-id"])

        return {
            "status": 200,
            "result": token
        }


class Verification(Resource):
    def __init__(self):
        self.reqparser = reqparse.RequestParser()
        self.reqparser.add_argument('mobile', type=str, location='args', required=True)

    def get(self):
        args = self.reqparser.parse_args()

        mobile = args["mobile"]

        verification_code = VerificationCode(mobile)
        if verification_code.request_count() >= settings["MAX_VERIFICATION_CODE_REQUEST_COUNT"]:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_MAX_REQUEST)

        code = verification_code.get_code()
        if not code:
            # get and send sms code
            code = mobile[-6:]
            verification_code.set_code(code)

        return {
            "status": 200,
            "result": {
                "verification_code": code
            }
        }


class Login(Resource):
    def __init__(self):
        self.reqparser = reqparse.RequestParser()
        self.reqparser.add_argument('device-id', dest='device_id', type=str,
                                    location='headers', required=True)
        self.reqparser.add_argument('mobile', type=str, location='json', required=True)
        self.reqparser.add_argument('password', type=str, location='json', required=True)

    def post(self):
        args = self.reqparser.parse_args()
        device_id = args['device_id']
        mobile = args['mobile']
        password = args['password']
        user = User.find_by_mobile(mobile)
        if user is None:
            st_raise_error(ErrorCode.NOT_REGISTERED)
        elif not user.verify_password(password):
            raise st_raise_error(ErrorCode.USER_PASSWORD_WRONG)
        elif not user.is_available():
            raise st_raise_error(ErrorCode.USER_UNAVAILABLE)
        token = user.login_on(device_id)
        user_info = user.to_dict_with_mobile()
        user_info.update(token)
        user_info['work_experiences'] = work_service.get_work_experiences(user.id)
        return compose_response(result=user_info)


class RefreshToken(Resource):
    @refresh_token_required
    def get(self):
        return {
            "status": 200,
            "result": current_user.user.login_on(current_user.device_id)
        }

    post = get


class Logout(Resource):
    @login_required
    def get(self):
        current_user.user.logout()
        return {
            "status": 200
        }

    post = get


class SearchUsers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user_name', type=unicode, location='args', required=False)

    @login_required
    def get(self):
        args = self.reqparse.parse_args()
        users = User.search_users(args["user_name"])

        return {
            "status": 200,
            "result": {
                "users": users
            }
        }


class UserDetail(Resource):
    def __init__(self):
        self.reqparser = reqparse.RequestParser()
        self.reqparser.add_argument('user_name', type=unicode, location='json', required=False)
        self.reqparser.add_argument('gender', type=int, location='json', required=False)
        self.reqparser.add_argument('user_id', type=unicode, location='json', required=False)

    @login_required
    def post(self):
        args = self.reqparser.parse_args()
        user_info = current_user.user.update_user(**args)

        return {
            "status": 200,
            "result": user_info
        }

class UploadUserIcon(Resource):
    @login_required
    def post(self):
        img = request.files['image']
        img_name = secure_filename(img.filename)
        ext = img_name.split('.')[-1]
        user_id = current_user.user.id

        img_file = "{}.{}".format(md5(str(user_id), settings["SECRET_KEY"]), ext)
        saved_path = os.path.join(settings['UPLOAD_FOLDER'], img_file)
        img.save(saved_path)

        user_info = current_user.user.update_user(avatar=img_file)
        return {
            "status": 200,
            "result": user_info
        }


class UserProfile(Resource):
    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='args', required=True)
        args = reqparser.parse_args()
        uid = decode_id(args['uid'])
        user_profile = user_service.get_user_profile(uid)
        return compose_response(result=user_profile)
