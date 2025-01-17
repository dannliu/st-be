# -*- coding: utf-8 -*-
import os
from datetime import datetime
import time

from flask import request
from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse
from werkzeug.utils import secure_filename

from colleague.acl import login_required, refresh_token_required
from colleague.service.aliyun.aliyun_sms_service import send_sms_code
from colleague.config import settings
from colleague.extensions import db
from colleague.extensions import redis_conn
from colleague.models.endorsement import Endorsement
from colleague.models.user import User
from colleague.service import user_service, rc_service
from colleague.service.aliyun import aliyun_oss_service
from colleague.utils import (ErrorCode, VerificationCode, md5,
                             st_raise_error, decode_id, generate_random_verification_code)
from . import compose_response
import logging


class Register(Resource):

    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('device-id', type=str, location='headers', required=True)
        reqparser.add_argument('mobile', type=str, location='json', required=True)
        reqparser.add_argument('password', type=str, location='json', required=True)
        reqparser.add_argument('verification_code', type=str, location='json', required=True)
        args = reqparser.parse_args()

        mobile = args["mobile"]
        password = args["password"]

        verification_code = redis_conn.get("verification_code:{}".format(mobile))
        if verification_code is None:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_EXPIRE)
        if verification_code != args["verification_code"]:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_NOT_MATCH)

        user = User.find_by_mobile(mobile)
        message = ""
        if user is None:
            user = User.add(mobile, password)
            Endorsement.add(user.id)
            message = "注册成功"
        else:
            user.hash_password(password)
            db.session.commit()
            message = "密码已重置"
        token = user.login_on(args["device-id"])
        json_user = user_service.get_login_user_profile(user.id)
        json_user.update(token)
        return compose_response(result=json_user, message=message)


class Verification(Resource):

    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('mobile', type=str, location='args', required=True)
        args = reqparser.parse_args()

        mobile = args["mobile"]

        verification_code = VerificationCode(mobile)
        if verification_code.request_count() >= settings["MAX_VERIFICATION_CODE_REQUEST_COUNT"]:
            raise st_raise_error(ErrorCode.VERIFICATION_CODE_MAX_REQUEST)

        code = verification_code.get_code()
        if not code:
            # get and send sms code
            if os.getenv("API_ENV") == "dev" and mobile.startswith('190'):
                code = mobile[-6:]
            else:
                code = generate_random_verification_code()
                result = send_sms_code(mobile, code)
                if not result:
                    st_raise_error(ErrorCode.VERIFICATION_CODE_SEND_FAILED)
            verification_code.set_code(code)
        return compose_response(message="验证码已发送")


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
        json_user = user_service.get_login_user_profile(user.id)
        json_user.update(token)
        return compose_response(result=json_user, message="登录成功")


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
    def post(self):
        current_user.user.logout()
        return compose_response()


class SearchUsers(Resource):

    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('user_name', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        users = User.search_users(args["user_name"])
        return compose_response(result={"users": users})


class UserDetail(Resource):
    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('user_name', type=unicode, location='json', required=False)
        reqparser.add_argument('gender', type=int, location='json', required=False)
        reqparser.add_argument('colleague_id', type=unicode, location='json', required=False)
        args = reqparser.parse_args()
        user_info = current_user.user.update_user(**args)
        login_user = User.find(current_user.user.id)
        rc_service.refresh_user_info(login_user)
        return {
            "status": 200,
            "result": user_info
        }


class UploadAvatar(Resource):
    @login_required
    def post(self):
        img = request.files['image']
        img_name = secure_filename(img.filename)
        ext = img_name.split('.')[-1]
        user_id = current_user.user.id
        date = datetime.now()
        date_dir = "{}/{}/{}".format(date.year, date.month, date.day)
        saved_dir = os.path.join(settings['UPLOAD_FOLDER'], date_dir)
        # if not os.path.exists(saved_dir):
        #     try:
        #         # Don't use os.path.exists, two processes may create the folder
        #         # at the same time
        #         os.makedirs(saved_dir)
        #     except:
        #         pass

        # Fix bug, change the avatar url when upload, as client will cache
        # the avatar using url as key
        img_file = "{}.{}".format(md5(str(user_id), str(time.time())), ext)
        saved_path = os.path.join(saved_dir, img_file)
        # img.save(saved_path)
        print ">>>>>> upload avatar, saved path = {}".format(saved_path)
        logging.info(">>>>>> Upload path %s", saved_path)
        aliyun_oss_service.upload_file(saved_path, img)

        user_info = current_user.user.update_user(avatar=saved_path)
        login_user = User.find(current_user.user.id)
        rc_service.refresh_user_info(login_user)
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
        uid = int(decode_id(args['uid']))
        user_profile = user_service.get_user_profile(uid, current_user.user.id)
        return compose_response(result=user_profile)


class MeProfile(Resource):
    @login_required
    def get(self):
        user_profile = user_service.get_login_user_profile(current_user.user.id)
        return compose_response(result=user_profile)


class RongCloud(Resource):
    """Get RongCloud token
    https://www.rongcloud.cn/docs/ios.html
    """

    @login_required
    def get(self):
        token = rc_service.get_rc_token(current_user.user)
        if token is None:
            st_raise_error(ErrorCode.RCTOKEN_FETCH_ERROR)
        return compose_response(result={"token": token})
