# -*- coding: utf-8 -*-

from datetime import datetime

import arrow
from flask_jwt_extended import create_access_token, create_refresh_token
from passlib.context import CryptContext

from colleague.config import settings
from colleague.extensions import db
from colleague.utils import ApiException, ErrorCode


pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=5000
)


class UserStatus(object):
    New = 0
    Confirmed = 1  # after confirmed by sms
    Blocked = 2
    Deleted = 3
    Logout = 4


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    mobile = db.Column(db.String(50), nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)

    user_name = db.Column(db.String(256))
    gender = db.Column(db.Integer)
    avatar = db.Column(db.String(1024))
    user_id = db.Column(db.Text)

    status = db.Column(db.Integer)

    current_organization_id = db.Column(db.BigInteger, db.ForeignKey('organizations.id'))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def find_user(user_id):
        return User.query.filter(User.id == user_id).one_or_none()

    @staticmethod
    def find_user_mobile(mobile):
        return User.query.filter(User.mobile == mobile).one_or_none()

    @staticmethod
    def add_user(mobile, password):
        user = User(mobile=mobile, status=UserStatus.Confirmed)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()

        return user

    def update_user(self, **kwargs):
        if not kwargs:
            return

        for key, value in kwargs.iteritems():
            if key in ["password", "user_name", "gender", "user_id", "avatar"]:
                if key == 'password':
                    self.hash_password(value)
                if key == 'user_id':
                    exist_user_id = User.query.filter(User.user_id == value).one_or_none()
                    if exist_user_id:
                        raise ApiException(ErrorCode.ALREADY_EXIST_USER_ID, "please user other user id.")
                else:
                    setattr(self, key, value)

        db.session.commit()

        return self.to_dict()

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def login_on(self, device_id):
        self.last_login_at = arrow.utcnow().naive
        self.status = UserStatus.Confirmed
        db.session.commit()

        payload = self._generate_token_metadata(device_id)
        access_token = create_access_token(identity=payload)
        refresh_token = create_refresh_token(identity=payload)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def _generate_token_metadata(self, device_id):
        return {
            'user_id': self.id,
            'device_id': device_id,
            'timestamp': arrow.get(self.last_login_at).timestamp
        }

    def verify_token_metadata(self, metadata, device_id):
        expected = self._generate_token_metadata(device_id)
        return metadata == expected

    def is_available(self):
        return self.status not in [UserStatus.Blocked, UserStatus.Deleted]

    def is_logged_out(self):
        return self.status == UserStatus.Logout

    def logout(self):
        self.status = UserStatus.Logout
        db.session.commit()

    def to_dict(self):
        return {
            "mobile": self.mobile,
            "user_name": self.user_name,
            "gender": self.gender,
            "avatar": "https://{}/{}".format(settings["SERVER_NAME"], self.avatar) if self.avatar else "",
            "user_id": self.user_id
        }


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    name = db.Column(db.String(256))
    icon = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verified = db.Column(db.Boolean)
