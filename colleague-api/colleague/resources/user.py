# -*- coding: utf-8 -*-
import os

from flask import request

from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse
from werkzeug.utils import secure_filename

from colleague.acl import login_required, refresh_token_required
from colleague.config import settings
from colleague.extensions import redis_conn
from colleague.models.user import User, WorkExperience
from colleague.utils import ApiException, ErrorCode, VerificationCode, md5


class Register(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('device-id', type=str, location='headers', required=True)
        self.reqparse.add_argument('mobile', type=str, location='json', required=True)
        self.reqparse.add_argument('password', type=str, location='json', required=True)
        self.reqparse.add_argument('verification_code', type=str, location='json', required=True)

    def post(self):
        args = self.reqparse.parse_args()

        mobile = args["mobile"]
        password = args["password"]

        user = User.find_user_mobile(mobile)
        if user:
            raise ApiException(ErrorCode.ALREADY_EXIST_MOBILE, "该手机号已被注册")

        verification_code = redis_conn.get("verification_code:{}".format(mobile))
        if verification_code is None:
            raise ApiException(ErrorCode.VERIFICATION_CODE_EXPIRE, "验证码已过期")
        if verification_code != args["verification_code"]:
            raise ApiException(ErrorCode.VERIFICATION_CODE_NOT_MATCH, "验证码错误")

        user = User.add_user(mobile, password)
        token = user.login_on(args["device-id"])

        return {
            "status": 200,
            "result": token
        }


class Verification(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('mobile', type=str, location='args', required=True)

    def get(self):
        args = self.reqparse.parse_args()

        mobile = args["mobile"]

        verification_code = VerificationCode(mobile)
        if verification_code.request_count() >= settings["MAX_VERIFICATION_CODE_REQUEST_COUNT"]:
            raise ApiException(ErrorCode.VERIFICATION_CODE_MAX_REQUEST, "please request later.")

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
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('device-id', dest='device_id', type=str,
                                   location='headers', required=True)
        self.reqparse.add_argument('mobile', type=str, location='json', required=True)
        self.reqparse.add_argument('password', type=str, location='json', required=True)

    def post(self):
        args = self.reqparse.parse_args()
        device_id = args['device_id']
        mobile = args['mobile']
        password = args['password']
        user = User.find_user_mobile(mobile)
        if user is None:
            raise ApiException(ErrorCode.NON_EXIST_USER, "还没有注册，快去注册吧")
        elif not user.verify_password(password):
            raise ApiException(ErrorCode.USER_PASSWORD_WRONG, "密码错误")
        elif not user.is_available():
            raise ApiException(ErrorCode.USER_UNAVAILABLE, "用户已被禁止访问")
        token = user.login_on(device_id)
        user_info = user.to_dict()
        user_info.update(token)

        return {
            "status": 200,
            "result": {
                'user': user_info,
                'user_details': {
                    'work_experiences': WorkExperience.get_all_work_experiences(user.id)
                }
            }
        }


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
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user_name', type=unicode, location='json', required=False)
        self.reqparse.add_argument('gender', type=int, location='json', required=False)
        self.reqparse.add_argument('user_id', type=unicode, location='json', required=False)

    @login_required
    def post(self):
        args = self.reqparse.parse_args()
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
