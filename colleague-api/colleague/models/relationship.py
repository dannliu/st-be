# -*- coding:utf-8 -*-

from datetime import datetime
import arrow

from colleague.extensions import db
from colleague.models.user import User
from colleague.models.work import WorkExperience
from colleague.utils import list_to_dict, decode_id, st_raise_error, ErrorCode


class RelationshipRequestType(object):
    # Added by user
    Added = 1

    # Recommended by others
    Recommended = 2


class RelationshipStatus(object):
    Removed = 0
    Normal = 1


class RelationshipRequestStatus(object):
    Pending = 0
    Accept = 1
    Reject = 2


class Relationship(db.Model):
    __tablename__ = 'relationship'
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
                        Relationship.status == RelationshipStatus.Normal) \
                .order_by(db.desc(Relationship.updated_at)).offset(0).limit(size)
        else:
            last_update = decode_id(cursor)
            contacts = Relationship.query \
                .filter(Relationship.uid_one == from_uid or Relationship.uid_two,
                        Relationship.status == RelationshipStatus.Normal,
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
        if type == RelationshipRequestType.Added:
            relationship.type = RelationshipRequestType.Added
        relationship.status = RelationshipStatus.Normal
        relationship.updated_at = arrow.utcnow().naive

        db.session.commit()

    @staticmethod
    def find_relationship(user_one, user_two):
        uid_one, uid_two = sorted([user_one, user_two])
        return Relationship.query.filter(Relationship.uid_one == uid_one,
                                         Relationship.uid_two == uid_two).one_or_none()


class RelationshipRequest(db.Model):
    """
    关系请求。
    关系请求目前分为两种: 1, 用户主动添加. 2: 用户推荐认识
    uid: 关系发起者，如果是主动添加，则为主动添加的用户。如果是推荐，则为推荐人
    uidA: 关系的一方，如果是主动添加，则为主动添加人uid, 可以理解为A 把自己推荐给 B。如果是推荐，则为被推荐人
    uidB: 关系的一方，关系的接受者
    """
    __tablename__ = 'relationship_request'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    # 如果用户主动添加，uidA = 用户id，可以理解为用户把自己推荐给 B
    # 如果用户推荐 A 给 B, 就按照字面解释
    uid = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, comment=u"请求发起者")
    uidA = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, comment=u"被推荐人")
    uidB = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, comment=u"被添加人")
    type = db.Column(db.Integer, nullable=False, comment=u"1：添加，2：推荐")
    status = db.Column(db.Integer, nullable=False, default=0, comment=u"0:pending, 1: 接受, 2:拒绝")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_at = db.Column(db.DateTime, comment=u"接受/拒绝 时间")

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "uidA": self.uidA,
            "uidB": self.uidB,
            "type": self.type,
            "status": self.status
        }

    @staticmethod
    def get_by_cursor(uid, last_id, size):
        if last_id:
            requests = RelationshipRequest.query \
                .filter(RelationshipRequest.uidB == uid, RelationshipRequest.id < last_id) \
                .order_by(db.desc(RelationshipRequest.id)) \
                .offset(0) \
                .limit(size)
        else:
            requests = RelationshipRequest.query \
                .filter(RelationshipRequest.uidB == uid) \
                .order_by(db.desc(RelationshipRequest.id)) \
                .offset(0) \
                .limit(size)

        pass

    @staticmethod
    def add(uid, uidA, uidB):
        relationship = Relationship.find_relationship(uidA, uidB)
        if relationship and relationship.status == RelationshipStatus.Normal:
            st_raise_error(ErrorCode.RELATIONSHIP_ALREADY_CONNECTED)

        type = RelationshipRequestType.Added if uid == uidA else RelationshipRequestType.Recommended
        if type == RelationshipRequestType.Added:
            # the two user must have been in at least one same company if add directly.
            work_experiences_A = set(WorkExperience.get_company_ids(uidA))
            work_experiences_B = set(WorkExperience.get_company_ids(uidB))
            if len(work_experiences_A & work_experiences_B) == 0:
                st_raise_error(ErrorCode.ADD_RELATIONSHIP_NOT_COMMON_COMPANY)

        request = RelationshipRequest.query.filter(
                RelationshipRequest.uid == uid,
                RelationshipRequest.uidA == uidA,
                RelationshipRequest.uidB == uidB,
        ).one_or_none()

        if request is None:
            request = RelationshipRequest(uid=uid, uidA=uidA, uidB=uidB, type=type,
                                          status=RelationshipRequestStatus.Pending)
            db.session.add(request)

        db.session.commit()

        return request.to_dict()

    @staticmethod
    def complete(uid, id, accept):
        # You must filter with id and uidB to ensure that this is done by the uidB
        request = RelationshipRequest.query.filter(RelationshipRequest.id == id,
                                                   RelationshipRequest.uidB == uid).one_or_none()
        if request:
            request.status = RelationshipRequestStatus.Accept if accept else RelationshipRequestStatus.Reject
            request.end_at = arrow.utcnow().naive
            db.session.commit()
            if accept:
                Relationship.add(request.uidA, request.uidB, request.type)
