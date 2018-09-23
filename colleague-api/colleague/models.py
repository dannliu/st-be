# -*- coding: utf-8 -*-

from datetime import datetime

import arrow
from flask_jwt_extended import create_access_token, create_refresh_token
from passlib.context import CryptContext

from colleague.config import settings
from colleague.extensions import db
from colleague.utils import ApiException, ErrorCode, decode_cursor, encode_cursor, list_to_dict

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
    def find_user_by_ids(uids):
        return User.query.filter(User.id.in_(uids)).all()

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
            if key in ["password", "user_name", "gender", "user_id", "avatar"] and value:
                if key == 'password':
                    self.hash_password(value)
                if key == 'user_id':
                    exist_user_id = User.query.filter(User.user_id == value).one_or_none()
                    if exist_user_id:
                        raise ApiException(ErrorCode.ALREADY_EXIST_USER_ID, "please user other user id.")
                    self.user_id = value
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
            "avatar": "{}/images/avatar/{}".format(settings["SERVER_NAME"], self.avatar) if self.avatar else "",
            "user_id": self.user_id
        }


class ContactType(object):
    Added = 1,
    Recommened = 2,


class ContactStatus(object):
    Removed = 0,
    Normal = 1,


class Relationships(db.Model):
    __tablename__ = 'relationships'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid_one = db.Column(db.BigInteger, nullable=False)
    uid_two = db.Column(db.BigInteger, nullable=False)
    # todo: do we need to record the recommend user here?
    status = db.Column(db.Integer, nullable=False, comment=u'0: 已删除, 1: 正常')
    type = db.Column(db.Integer, nullable=False, comment=u'1: 自己添加, 2: 熟人推荐')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'第一次添加时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'更新时间')
    removed_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def get_by_cursor(from_uid, cursor, size):
        if cursor:
            contacts = Relationships.query \
                .filter(Relationships.uid_one == from_uid or Relationships.uid_two == from_uid,
                        Relationships.status == ContactStatus.Normal) \
                .order_by(db.desc(Relationships.updated_at)).offset(0).limit(size)
        else:
            last_update = decode_cursor(cursor)
            contacts = Relationships.query \
                .filter(Relationships.uid_one == from_uid or Relationships.uid_two,
                        Relationships.status == ContactStatus.Normal,
                        Relationships.updated_at < last_update) \
                .order_by(db.desc(Relationships.updated_at)).offset(0).limit(size)
        uids = set()
        for contact in contacts:
            uids.add(contact.uid_one)
            uids.add(contact.uid_two)
        users = User.find_user_by_ids(uids)
        # todo: do we need to fetch the user from redis?
        dict_users = list_to_dict(users, "id")
        json_contacts = []
        for contact in contacts:
            uid = contact.uid_one == from_uid and contact.uid_two or contact.uid_one
            user = dict_users.get(uid)
            if user:
                json_contacts.append({
                    'user': user.to_dict(),
                    'type': contact.type,
                    'update_at': contact.updated_at
                })
        return json_contacts


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    name = db.Column(db.String(256))
    icon = db.Column(db.TEXT)
    verified = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def add(name, icon=None, verified=False):
        og = Organization.query.filter(Organization.name == name).one_or_none()
        if og:
            return og
        else:
            og = Organization(name=name, icon=icon, verified=verified)
            db.session.add(og)
            db.session.commit()
            return og

    @staticmethod
    def find_by_id(id):
        return Organization.query(Organization.id == id).one_or_none()

    def to_dict(self):
        return {
            "id": encode_cursor(self.id),
            "name": self.name,
            "icon": self.icon
        }


class WorkExperience(db.Model):
    __tablename__ = "work_experience"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uid = db.Column(db.BigInteger, index=True, nullable=False)
    start_year = db.Column(db.SMALLINT, nullable=False, comment=u'开始-年')
    start_month = db.Column(db.SMALLINT, nullable=False, comment=u'开始-月')
    end_year = db.Column(db.SMALLINT, nullable=True, comment=u'2999表示至今')
    end_month = db.Column(db.SMALLINT, nullable=True)
    title = db.Column(db.String(255), nullable=False, comment=u'职位')
    company_id = db.Column(db.BigInteger, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    delete_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def add(new_one):
        db.session.add(new_one)
        db.session.commit()

    def to_dict(self):
        return {
            "id": encode_cursor(self.id),
            "start_year": self.start_year,
            "start_month": self.start_month,
            "end_year": self.end_year,
            "end_month": self.end_month,
            "title": self.title
        }
