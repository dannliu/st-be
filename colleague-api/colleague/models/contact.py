# -*- coding:utf-8 -*-

from datetime import datetime
import arrow

from colleague.extensions import db
from colleague.models.user import User
from colleague.models.work import WorkExperience
from colleague.utils import (list_to_dict, decode_id, st_raise_error,
                             ErrorCode, datetime_to_timestamp)


class ContactStatus(object):
    Connected = 0
    Removed = 1


class ContactRequestType(object):
    # Added by user
    Added = 1

    # Recommended by others
    Recommended = 2


class ContactRequestStatus(object):
    Pending = 0
    Accepted = 1
    # Which means deleted
    Rejected = 2


class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uidA = db.Column(db.BigInteger, name="uid_a", nullable=False)
    uidB = db.Column(db.BigInteger, name="uid_b", nullable=False)
    status = db.Column(db.Integer, nullable=False, comment=u'0: 已删除, 1: 正常', default=1)
    type = db.Column(db.Integer, nullable=False, comment=u'1: 自己添加, 2: 熟人推荐')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'第一次添加时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment=u'更新时间')
    removed_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def find_by_cursor(from_uid, cursor, size):
        if cursor:
            contacts = Contact.query \
                .filter(Contact.uidA == from_uid or Contact.uidB == from_uid,
                        Contact.status == ContactStatus.Connected) \
                .order_by(db.desc(Contact.updated_at)).offset(0).limit(size)
        else:
            last_update = decode_id(cursor)
            contacts = Contact.query \
                .filter(Contact.uidA == from_uid or Contact.uidB,
                        Contact.status == ContactStatus.Connected,
                        Contact.updated_at < last_update) \
                .order_by(db.desc(Contact.updated_at)).offset(0).limit(size)
        uids = set()
        for contact in contacts:
            uids.add(contact.uidA)
            uids.add(contact.uidB)
        users = User.find_by_ids(uids)
        # todo: do we need to fetch the user from redis?
        dict_users = list_to_dict(users, "id")
        json_contacts = []
        for contact in contacts:
            uid = contact.uidA == from_uid and contact.uidB or contact.uidA
            user = dict_users.get(uid)
            if user:
                json_contacts.append({
                    'user': user.to_dict(),
                    'type': contact.type,
                    'update_at': contact.updated_at
                })
        return json_contacts

    @staticmethod
    def add(uidA, uidB, type):
        contact = Contact.find_by_uid(uidA, uidB)
        if contact is None:
            uidA, uidB = sorted([uidA, uidB])
            contact = Contact(uidA=uidA, uidB=uidB, type=type)
            db.session.add(contact)
        # 由于联系人的请求有两种来源：自己添加和朋友推荐
        # 这两种情况可能同时会存在，但是以用户添加为主
        if type == ContactRequestType.Added:
            contact.type = ContactRequestType.Added
        contact.status = ContactStatus.Connected
        contact.updated_at = arrow.utcnow().naive
        db.session.commit()

    @staticmethod
    def find_by_uid(uidA, uidB):
        uidA, uidB = sorted([uidA, uidB])
        return Contact.query.filter(Contact.uidA == uidA,
                                    Contact.uidB == uidB).one_or_none()


class ContactRequest(db.Model):
    """
    关系请求。
    关系请求目前分为两种: 1, 用户主动添加. 2: 用户推荐认识
    uid:  关系发起者，如果是主动添加，则为主动添加的用户。如果是推荐，则为推荐人
    uidA: 关系的一方，如果是主动添加，则为主动添加人uid, 可以理解为A 把"自己"推荐给 B。如果是推荐，则为被推荐人
    uidB: 关系的一方，关系的接受者
    """
    __tablename__ = 'contact_request'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    # 如果用户主动添加，uidA = 用户id，可以理解为用户把自己推荐给 B
    # 如果用户推荐 A 给 B, 就按照字面解释
    uid = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, comment=u"请求发起者")
    uidA = db.Column(db.BigInteger, db.ForeignKey("users.id"), name="uid_a", nullable=False, comment=u"被推荐人")
    uidB = db.Column(db.BigInteger, db.ForeignKey("users.id"), name="uid_b", nullable=False, comment=u"被添加人")
    type = db.Column(db.Integer, nullable=False, comment=u"1：添加，2：推荐")
    status = db.Column(db.Integer, nullable=False, default=0, comment=u"0:pending, 1: 接受, 2:拒绝")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_at = db.Column(db.DateTime, comment=u"接受/拒绝 时间")

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.to_dict(),
            "userA": self.userA.to_dict(),
            "userB": self.userB.to_dict(),
            "type": self.type,
            "status": self.status,
            "create_at": datetime_to_timestamp(self.created_at)
        }

    @staticmethod
    def find_by_cursor(uid, last_id, size=20):
        if last_id:
            requests = ContactRequest.query \
                .filter(ContactRequest.uidB == uid,
                        ContactRequest.status == ContactRequestStatus.Accepted or ContactRequestStatus == ContactRequestStatus.Pending,
                        ContactRequest.id < last_id) \
                .order_by(db.desc(ContactRequest.id)) \
                .offset(0) \
                .limit(size).all()
        else:
            requests = ContactRequest.query \
                .filter(ContactRequest.uidB == uid,
                        ContactRequest.status == ContactRequestStatus.Accepted or ContactRequest.status == ContactRequestStatus.Pending) \
                .order_by(db.desc(ContactRequest.id)) \
                .offset(0) \
                .limit(size).all()
        return requests

    @staticmethod
    def add(uid, uidA, uidB):
        relationship = Contact.find_by_uid(uidA, uidB)
        if relationship and relationship.status == ContactStatus.Connected:
            st_raise_error(ErrorCode.RELATIONSHIP_ALREADY_CONNECTED)

        type = ContactRequestType.Added if uid == uidA else ContactRequestType.Recommended
        if type == ContactRequestType.Added:
            # the two user must have been in at least one same company if add directly.
            work_experiences_A = set(WorkExperience.get_company_ids(uidA))
            work_experiences_B = set(WorkExperience.get_company_ids(uidB))
            if len(work_experiences_A & work_experiences_B) == 0:
                st_raise_error(ErrorCode.ADD_RELATIONSHIP_NOT_COMMON_COMPANY)

        request = ContactRequest.query.filter(
                ContactRequest.uid == uid,
                ContactRequest.uidA == uidA,
                ContactRequest.uidB == uidB,
        ).one_or_none()

        if request is None:
            request = ContactRequest(uid=uid, uidA=uidA, uidB=uidB, type=type,
                                     status=ContactRequestStatus.Pending)
            db.session.add(request)

        db.session.commit()

        return request.to_dict()

    @staticmethod
    def complete(uid, id, accept):
        # You must filter with id and uidB to ensure that this is done by the uidB
        request = ContactRequest.query.filter(ContactRequest.id == id,
                                              ContactRequest.uidB == uid).one_or_none()
        if request and request.status == ContactRequestStatus.Pending:
            request.status = ContactRequestStatus.Accepted if accept else ContactRequestStatus.Rejected
            request.end_at = arrow.utcnow().naive
            db.session.commit()
            if accept:
                Contact.add(request.uidA, request.uidB, request.type)