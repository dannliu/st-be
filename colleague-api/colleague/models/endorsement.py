# -*- coding:utf-8 -*-

from datetime import datetime

import arrow

from colleague.extensions import db
from colleague.utils import (encode_id, datetime_to_timestamp, ErrorCode, st_raise_error)


class EndorseType:
    # 大牛
    Niubility = 1
    # 靠谱
    Reliability = 2

    @staticmethod
    def check(type):
        return type == EndorseType.Niubility or type == EndorseType.Reliability


class EndorseStatus:
    Supported = 0,
    Removed = 1


# It's an overall state of endorsement
class Endorsement(db.Model):
    __tablename__ = 'endorsement'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_contacts = db.Column(db.Integer, nullable=False, default=0)
    niubility = db.Column(db.Integer, nullable=False, default=0)
    reliability = db.Column(db.Integer, nullable=False, default=0)

    @staticmethod
    def add_new_one(uid):
        # When create a new user, must create a endorsement accordingly
        endorsement = Endorsement(uid=uid)
        db.session.add(endorsement)
        db.session.commit()

    @staticmethod
    def find_by_uid(uid):
        return Endorsement.query.filter(Endorsement.uid == uid).one_or_none()

    @staticmethod
    def update_niubility_count(uid, cnt):
        Endorsement._update_count(uid, "niubility", cnt)

    @staticmethod
    def update_reliability_count(uid, cnt):
        Endorsement._update_count(uid, "reliability", cnt)

    @staticmethod
    def update_total_contacts_count(uid, cnt):
        Endorsement._update_count(uid, "total_contacts", cnt)

    @staticmethod
    def _update_count(uid, attr, cnt):
        if abs(cnt) != 1:
            # cnt must be 1 or -1
            return
        endorsement = Endorsement.query.filter(Endorsement.uid == uid).one_or_none()
        if endorsement:
            count = getattr(endorsement, attr) + cnt
            if count >= 0:
                setattr(endorsement, attr, count)
                db.session.commit()

    def to_dict(self):
        return {
            "total_contacts": self.total_contacts,
            "niubility_count": self.niubility,
            "reliability_count": self.reliability
        }


class UserEndorse(db.Model):
    __tablename__ = 'user_endorse'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment=u"to uid")
    from_uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment=u"from uid")
    fromUser = db.relationship('colleague.models.user.User', foreign_keys=from_uid, lazy="selectin")
    type = db.Column(db.SMALLINT, nullable=False, comment=u"1: 大牛, 2: 靠谱")
    status = db.Column(db.SMALLINT, nullable=False, comment=u"0: 开启, 1: 取消")
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    db.UniqueConstraint(uid, from_uid, type)

    @staticmethod
    def find_by_from_uid(uid, from_uid, type):
        return UserEndorse.query \
            .filter(UserEndorse.uid == uid,
                    UserEndorse.from_uid == from_uid,
                    UserEndorse.type == type,
                    UserEndorse.status == EndorseStatus.Supported) \
            .one_or_none()

    @staticmethod
    def find_by_cursor(uid, type, latest_id, size):
        if latest_id:
            return UserEndorse.query \
                .filter(UserEndorse.uid == uid,
                        UserEndorse.type == type,
                        UserEndorse.status == EndorseStatus.Supported,
                        UserEndorse.id > latest_id) \
                .order_by(db.desc(UserEndorse.id)) \
                .offset(0).limit(size).all()
        else:
            return UserEndorse.query \
                .filter(UserEndorse.uid == uid,
                        UserEndorse.type == type,
                        UserEndorse.status == EndorseStatus.Supported) \
                .order_by(db.desc(UserEndorse.id)) \
                .offset(0).limit(size).all()

    def to_dict(self):
        return {
            'id': encode_id(self.id),
            'from_user': self.fromUser.to_dict(),
            'type': self.type,
            'create_at': datetime_to_timestamp(self.create_at)
        }


    @staticmethod
    def update(uid, from_uid, type, status):
        endorse = UserEndorse.query.filter(UserEndorse.uid == uid,
                                           UserEndorse.from_uid == from_uid,
                                           UserEndorse.type == type).one_or_none()
        endorse_status = EndorseStatus.Supported if status else EndorseStatus.Removed
        if endorse and endorse.status == endorse_status:
            # duplicate request
            return
        if endorse_status == EndorseStatus.Removed and not endorse:
            # endorse must be existed when u tries to remove
            return
        if not endorse:
            endorse = UserEndorse(uid=uid, from_uid=from_uid, type=type)
            db.session.add(endorse)
        endorse.status = endorse_status
        endorse.update_at = arrow.utcnow().naive
        cnt = 1 if endorse_status == EndorseStatus.Supported else -1
        if type == EndorseType.Niubility:
            Endorsement.update_niubility_count(uid, cnt)
        elif type == EndorseType.Reliability:
            Endorsement.update_reliability_count(uid, cnt)
        db.session.commit()


class EndorseComment(db.Model):
    __tablename__ = 'endorse_comment'
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment=u"to uid")
    # user = db.relationship('colleague.models.user.User', foreign_keys=[uid])
    from_uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment=u"from uid")
    from_user = db.relationship('colleague.models.user.User', foreign_keys=from_uid, lazy="selectin")
    text = db.Column(db.TEXT, nullable=True)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    db.UniqueConstraint(uid, from_uid)

    @staticmethod
    def update(uid, from_uid, text):
        comment = EndorseComment.query.filter(EndorseComment.uid == uid,
                                              EndorseComment.from_uid == from_uid).one_or_none()
        if not comment:
            comment = EndorseComment(uid=uid, from_uid=from_uid)
            db.session.add(comment)
        comment.update_at = arrow.utcnow().naive
        comment.text = text
        db.session.commit()

    @staticmethod
    def find_by_from_uid(uid, from_uid):
        return EndorseComment.query \
            .filter(EndorseComment.uid == uid, EndorseComment.from_uid == from_uid) \
            .one_or_none()

    @staticmethod
    def find_latest_by_uid(uid):
        return EndorseComment.query \
            .filter(EndorseComment.uid == uid) \
            .order_by(db.desc(EndorseComment.id)) \
            .first()

    def to_dict(self):
        return {
            'id': encode_id(self.id),
            'from_user': self.from_user.to_dict(),
            'text': self.text,
            'update_at': datetime_to_timestamp(self.update_at)
        }
