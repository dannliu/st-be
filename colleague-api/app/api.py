# -*- coding: utf-8 -*-

from datetime import datetime

import jwt
from flask import current_app, jsonify
from flask_restful import Resource, reqparse
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError
from sqlalchemy.orm.exc import NoResultFound

from .errors import APIException, APIErrors
from .extensions import db
from .models import User, UserStatus
from .utils import check_password, timestamp
from enum import Enum


class TestUser(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user', type=str, location='args', required=True)

    def get(self):
        args = self.reqparse.parse_args()
        return {'user': args["user"]}


class Login(Resource):
    TOKEN_ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXP_DURATION_MINUTES = 60 * 24  # 1d
    REFRESH_TOKEN_EXP_DURATION_MINUTES = 60 * 24 * 30  # 30d
    LOGIN_TYPE = Enum('LoginType', ['login', 'refresh'])

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('device-id', dest='device_id', type=str,
                                   location='headers', required=True)
        self.reqparse.add_argument('type', type=str, location='json',
                                   choices=[t.name for t in Login.LOGIN_TYPE],
                                   required=True)
        self.reqparse.add_argument('mobile', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')
        self.reqparse.add_argument('refresh_token', type=str, location='json')

    def post(self):
        args = self.reqparse.parse_args()
        device_id = args['device_id']
        login_type = args['type']
        if Login.LOGIN_TYPE.login.name == login_type:
            mobile = args['mobile']
            password = args['password']
            if mobile is None or password is None:
                raise APIException(*APIErrors.PARAMETER_MISSING, result={
                    'required': ['mobile', 'password']
                })
            try:
                user = db.session.query(User).filter(User.mobile == mobile).one()
            except NoResultFound:
                raise APIException(*APIErrors.UNREGISTERED_USER, result={'mobile': mobile})
            if not check_password(user.password_hash, password):
                raise APIException(*APIErrors.PASSWORD_INCORRECT)

        elif Login.LOGIN_TYPE.refresh.name == login_type:
            refresh_token = args['refresh_token']
            if refresh_token is None:
                raise APIException(*APIErrors.PARAMETER_MISSING, result={
                    'required': ['refresh_token']
                })
            metadata = Login.get_metadata_from_token(refresh_token, current_app.config["SECRET_KEY"])
            if device_id != metadata['device_id'] \
                    or 'refresh_token' != metadata['type']:
                raise APIException(*APIErrors.TOKEN_INVALID)
            try:
                user = db.session.query(User).filter(User.id == metadata['user_id']).one()
            except NoResultFound:
                raise APIException(*APIErrors.TOKEN_INVALID)
            if UserStatus.Login != user.status \
                    or timestamp(user.last_login_at) != metadata['timestamp']:
                raise APIException(*APIErrors.TOKEN_INVALID)

        token = self.login(user, device_id)
        return api_response(token)

    @staticmethod
    def login(user, device_id):
        user.last_login_at = datetime.utcnow()
        user.status = UserStatus.Login
        db.session.commit()

        metadata = {'user_id': user.id,
                    'device_id': device_id,
                    'timestamp': timestamp(user.last_login_at)}
        access_exp_time = metadata['timestamp'] + 60 * Login.ACCESS_TOKEN_EXP_DURATION_MINUTES
        refresh_exp_time = metadata['timestamp'] + 60 * Login.REFRESH_TOKEN_EXP_DURATION_MINUTES
        access_metadata = dict(metadata, exp=access_exp_time, type='access_token')
        refresh_metadata = dict(metadata, exp=refresh_exp_time, type='refresh_token')
        token = {
            'access_token': Login.generate_token(access_metadata, current_app.config["SECRET_KEY"]),
            'refresh_token': Login.generate_token(refresh_metadata, current_app.config["SECRET_KEY"])
        }
        return token

    @staticmethod
    def generate_token(metadata, secret_key):
        return jwt.encode(metadata, secret_key, algorithm=Login.TOKEN_ALGORITHM).decode('utf-8')

    @staticmethod
    def get_metadata_from_token(token, secret_key):
        try:
            decoded = jwt.decode(token, secret_key, algorithms=Login.TOKEN_ALGORITHM)
        except ExpiredSignatureError:
            raise APIException(*APIErrors.TOKEN_EXPIRED)
        except InvalidTokenError:
            raise APIException(*APIErrors.TOKEN_INVALID)
        return decoded


def api_response(result):
    response = jsonify({
        'status': 200,
        'result': result
    })
    return response
