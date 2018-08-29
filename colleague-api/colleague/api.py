# -*- coding: utf-8 -*-
import arrow

from flask import request, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.config import settings
from .extensions import redis_conn
from .models import User
from .utils import ApiException, ErrorCode, VerificationCode


class Register(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('mobile', type=str, location='json', required=True)
        self.reqparse.add_argument('password', type=str, location='json', required=True)
        self.reqparse.add_argument('verification_code', type=str, location='json', required=True)

    def post(self):
        args = self.reqparse.parse_args()

        mobile = args["mobile"]
        password = args["password"]

        user = User.find_user_mobile(mobile)
        if user:
            raise ApiException(ErrorCode.NON_EXIST_USER, "not exist user, please register first")

        verification_code = redis_conn.get("verification_code:{}".format(mobile))
        if verification_code is None:
            raise ApiException(ErrorCode.VERIFICATION_CODE_EXPIRE,
                               "your verification code is expired, please request again.")
        if verification_code != args["verification_code"]:
            raise ApiException(ErrorCode.VERIFICATION_CODE_NOT_MATCH, "wrong verification code.")

        user = User.add_user(mobile, password)

        # TODO: redirect to login
        data = {
            "user_id": user.id,
            "device_id": request.headers["device_id"],
            "timestamp": arrow.utcnow().timestamp,
        }

        access_token = create_access_token(identity=data)
        refresh_token = create_refresh_token(identity=data)

        return {
            "status": 200,
            "result": {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
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
            raise ApiException(ErrorCode.NON_EXIST_USER,
                               "not exist user, please register first")
        
        if not user.verify_password(password):
            raise ApiException(ErrorCode.USER_PASSWORD_WRONG,
                               "the password is wrong")

        token = user.login_on(device_id)
        return {
            "status": 200,
            "result": token
        }


class TestUser(Resource):
    @login_required
    def get(self):
        return {"user": current_user.user.id}
