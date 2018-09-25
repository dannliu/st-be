# -*- coding: utf-8 -*-

from datetime import datetime

import arrow
from flask_jwt_extended import create_access_token, create_refresh_token
from passlib.context import CryptContext
from sqlalchemy import or_

from colleague.config import settings
from colleague.extensions import db
from colleague.models.work import WorkExperience
from colleague.utils import ApiException, ErrorCode, decode_cursor, list_to_dict

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
    def search_users(search_string):
        if search_string.isdigit():
            mobile = search_string
            user = User.find_user_mobile(mobile)
            if user:
                return [user.to_dict()]
        else:
            users = User.query.filter(or_(User.user_name == search_string, User.user_id == search_string))
            return [user.to_dict() for user in users]

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
            "id": self.id,  # TODO: replace with user_id
            "mobile": self.mobile,
            "user_name": self.user_name,
            "gender": self.gender,
            "avatar": "{}/images/avatar/{}".format(settings["SERVER_NAME"], self.avatar) if self.avatar else "",
            "user_id": self.user_id
        }


class ContactType(object):
    Added = 1
    Recommened = 2


class ContactStatus(object):
    Removed = 0
    Normal = 1


class Relationship(db.Model):
    __tablename__ = 'relationships'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid_one = db.Column(db.BigInteger, nullable=False)
    uid_two = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.Integer, nullable=False, comment=u'0: 已删除, 1: 正常', default=1)
    type = db.Column(db.Integer, nullable=False, comment=u'1: 自己添加, 2: 熟人推荐')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'第一次添加时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'更新时间')
    removed_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def get_by_cursor(from_uid, cursor, size):
        if cursor:
            contacts = Relationship.query \
                .filter(Relationship.uid_one == from_uid or Relationship.uid_two == from_uid,
                        Relationship.status == ContactStatus.Normal) \
                .order_by(db.desc(Relationship.updated_at)).offset(0).limit(size)
        else:
            last_update = decode_cursor(cursor)
            contacts = Relationship.query \
                .filter(Relationship.uid_one == from_uid or Relationship.uid_two,
                        Relationship.status == ContactStatus.Normal,
                        Relationship.updated_at < last_update) \
                .order_by(db.desc(Relationship.updated_at)).offset(0).limit(size)
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

    @staticmethod
    def add(user_one, user_two, type):
        relationship = Relationship.find_relationship(user_one, user_two)
        if relationship is None:
            uid_one, uid_two = sorted([user_one, user_two])
            relationship = Relationship(uid_one=uid_one, uid_two=uid_two, type=type)
            db.session.add(relationship)

        # update to direct added
        if type == ContactType.Added:
            relationship.type = ContactType.Added
        relationship.status = ContactStatus.Normal
        relationship.updated_at = arrow.utcnow().naive

        db.session.commit()

    @staticmethod
    def find_relationship(user_one, user_two):
        uid_one, uid_two = sorted([user_one, user_two])
        return Relationship.query.filter(Relationship.uid_one == uid_one,
                                         Relationship.uid_two == uid_two).one_or_none()


class RelationshipRequestStatus(object):
    Pending = 0
    Accept = 1
    Reject = 2


class UserRelationshipRequest(db.Model):
    __tablename__ = 'user_relationship_requests'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    user_requester_id = db.Column(db.BigInteger, nullable=False)
    user_recommending_id = db.Column(db.BigInteger, nullable=False)
    user_being_recommended_id = db.Column(db.BigInteger, nullable=False)
    type = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "request_id": self.id,
            "requester": User.find_user(self.user_requester_id).to_dict(),
            "recommending_user": User.find_user(self.user_recommending_id).to_dict(),
            "being_recommended_user": User.find_user(self.user_being_recommended_id).to_dict(),
            "type": self.type,
            "status": self.status
        }

    @staticmethod
    def get_pending_requests(user_id):
        query = db.session.query(UserRelationshipRequest).filter(
            UserRelationshipRequest.user_being_recommended_id == user_id,
            UserRelationshipRequest.status == RelationshipRequestStatus.Pending)

        return [_.to_dict() for _ in query]

    @staticmethod
    def add(**kwargs):
        user_requester_id = kwargs["user_requester_id"]
        user_recommending_id = kwargs["user_recommending_id"]
        user_being_recommended_id = kwargs["user_being_recommended_id"]

        relationship = Relationship.find_relationship(user_recommending_id, user_being_recommended_id)
        if relationship and relationship.status == ContactStatus.Normal:
            # TODO: add notification
            raise ApiException(ErrorCode.ADD_RELATIONSHIP_NOT_COMMON_COMPANY, "could not add direct relationship.")

        type = ContactType.Added if user_requester_id == user_recommending_id else ContactType.Recommened
        if type == ContactType.Added:
            # the two user must have been in at least one same company if add directly.
            work_experiences_one = [_.company_id for _ in
                                    WorkExperience.query.filter(WorkExperience.uid == user_recommending_id)]
            work_experiences_two = [_.company_id for _ in
                                    WorkExperience.query.filter(WorkExperience.uid == user_recommending_id)]
            if len(set(work_experiences_one) & set(work_experiences_two)) == 0:
                raise ApiException(ErrorCode.ADD_RELATIONSHIP_NOT_COMMON_COMPANY, "could not add direct relationship.")

        requester = UserRelationshipRequest.query.filter(
            UserRelationshipRequest.user_requester_id == user_requester_id,
            UserRelationshipRequest.user_recommending_id == user_recommending_id,
            UserRelationshipRequest.user_being_recommended_id == user_being_recommended_id,
        ).one_or_none()

        if requester is None:
            requester = UserRelationshipRequest(
                user_requester_id=user_requester_id,
                user_recommending_id=user_recommending_id,
                user_being_recommended_id=user_being_recommended_id,
                type=type,
                status=RelationshipRequestStatus.Pending
            )
            db.session.add(requester)

        db.session.commit()

        return requester.to_dict()

    @staticmethod
    def complete(request_id, accept):
        # TODO: add notification
        requester = UserRelationshipRequest.query.filter(UserRelationshipRequest.id == request_id).one_or_none()
        if requester:
            requester.status = RelationshipRequestStatus.Accept if accept else RelationshipRequestStatus.Reject
            requester.end_at = arrow.utcnow().naive
            db.session.commit()

            if accept:
                Relationship.add(requester.user_recommending_id, requester.user_being_recommended_id, requester.type)