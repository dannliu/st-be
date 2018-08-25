# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

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


class TestUser(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user', type=str, location='args', required=True)

    def get(self):
        args = self.reqparse.parse_args()
        return {'user': args["user"]}


class Login(Resource):
    TOKEN_ALGORITHM = 'HS256'
    TOKEN_EXP_DURATION_MINUTES = 60 * 24 * 30   # 30d

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('mobile', type=str, location='json', required=True)
        self.reqparse.add_argument('password', type=str, location='json', required=True)
        self.reqparse.add_argument('device-id', dest='device_id', type=str, location='headers', required=True)

    def post(self):
        args = self.reqparse.parse_args()
        mobile = args['mobile']
        password = args['password']
        device_id = args['device_id']
        try:
            user = db.session.query(User).filter(User.mobile == mobile).one()
        except NoResultFound:
            raise APIException(*APIErrors.UNREGISTERED_USER, result={'mobile': mobile})
        if not check_password(user.password_hash, password):
            raise APIException(*APIErrors.PASSWORD_INCORRECT)
        token = self.login(user, device_id)
        return api_response({
            'token': token
        })

    @staticmethod
    def login(user, device_id):
        user.last_login_at = datetime.utcnow()
        user.status = UserStatus.Login
        db.session.commit()

        token_metadata = {'user_id': user.id,
                          'device_id': device_id,
                          'timestamp': timestamp(user.last_login_at)}
        token = Login.generate_access_token(token_metadata, current_app.config["SECRET_KEY"])
        return token

    @staticmethod
    def generate_access_token(metadata, secret_key, exp_duration_minutes=None):
        if not exp_duration_minutes:
            exp_duration_minutes = Login.TOKEN_EXP_DURATION_MINUTES
        exp_time = datetime.utcnow() + timedelta(minutes=exp_duration_minutes)
        metadata.update({
            'exp': exp_time
        })
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
