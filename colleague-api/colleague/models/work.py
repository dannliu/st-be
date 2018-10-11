# -*- coding:utf-8 -*-

from datetime import datetime

from colleague.extensions import db
from colleague.utils import encode_id


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    name = db.Column(db.String(255))
    icon = db.Column(db.TEXT)
    verified = db.Column(db.Boolean)
    alias = db.Column(db.String(255))
    info = db.Column(db.Text)
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
        return Organization.query.filter(Organization.id == id).one_or_none()

    @staticmethod
    def like(keyword, count):
        like_query = "%{}%".format(keyword)
        return Organization.query \
            .filter(Organization.name.like(like_query)) \
            .offset(0).limit(count).all()

    def to_dict(self):
        return {
            "id": encode_id(self.id),
            "name": self.name,
            "icon": self.icon
        }


class WorkExperienceStatus:
    Normal = 0
    Deleted = 1


class WorkExperience(db.Model):
    __tablename__ = "work_experience"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uid = db.Column(db.BigInteger, index=True, nullable=False)
    start_year = db.Column(db.SMALLINT, nullable=False, comment=u'开始-年')
    start_month = db.Column(db.SMALLINT, nullable=False, comment=u'开始-月')
    end_year = db.Column(db.SMALLINT, nullable=False, comment=u'2999表示至今')
    end_month = db.Column(db.SMALLINT, nullable=True)
    title = db.Column(db.String(255), nullable=False, comment=u'职位')
    company_id = db.Column(db.BigInteger, db.ForeignKey("organizations.id"), nullable=False)
    company = db.relationship("Organization")
    status = db.Column(db.SMALLINT, nullable=False, default=0, comment=u"0: normal, 1: deleted")
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    delete_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def add(new_one):
        db.session.add(new_one)
        db.session.commit()

    def update(self):
        db.session.commit()

    @staticmethod
    def find_by_uid_id(uid, id):
        return WorkExperience.query.filter(WorkExperience.id == id,
                                           WorkExperience.uid == uid).one_or_none()

    @staticmethod
    def find_all_for_user(uid):
        return WorkExperience.query.filter(WorkExperience.uid == uid,
                                           WorkExperience.status == WorkExperienceStatus.Normal).all()

    @staticmethod
    def get_company_ids(uid):
        return [_[0] for _ in
                WorkExperience.query.with_entities(db.distinct(WorkExperience.company_id)).filter(
                        WorkExperience.uid == uid,
                        WorkExperience.status == WorkExperienceStatus.Normal).all()]

    @staticmethod
    def delete(uid, id):
        we = WorkExperience.find_by_uid_id(uid, id)
        if we:
            we.status = WorkExperienceStatus.Deleted
            we.delete_date = datetime.utcnow()
            db.session.commit()

    def to_dict(self):
        return {
            "id": encode_id(self.id),
            "start_year": self.start_year,
            "start_month": self.start_month,
            "end_year": self.end_year,
            "end_month": self.end_month,
            "title": self.title,
            "company": self.company.to_dict()
        }
