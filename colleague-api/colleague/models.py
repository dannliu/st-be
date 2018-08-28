# -*- coding: utf-8 -*-

from datetime import datetime

from colleague.extensions import db


class UserStatus(object):
    New = 0
    Confirmed = 1  # after confirmed by sms
    Blocked = 2
    Deleted = 3


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    mobile = db.Column(db.String(50), nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)

    user_name = db.Column(db.String(256))
    gender = db.Column(db.Integer)
    avatar = db.Column(db.String(1024))

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

    def hash_password(self, password):
        # TODO:
        self.password_hash = password

    def verify_password(self, password):
        # TODO:
        return True


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    name = db.Column(db.String(256))
    icon = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verified = db.Column(db.Boolean)
