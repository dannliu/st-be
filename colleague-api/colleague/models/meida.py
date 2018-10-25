# -*- coding:utf-8 -*-

import os
from datetime import datetime

from colleague.extensions import db
from colleague.utils import list_to_dict, encode_id, decode_id


class MediaLocation(object):
    Local = 0,
    AliyunOSS = 1


class Image(db.Model):
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    path = db.Column(db.String(255), unique=True)
    location = db.Column(db.SMALLINT, default=0, comment="0:local, 1: aliyun oss")
    info = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def add(obj):
        db.session.add(obj)
        db.session.commit()

    @staticmethod
    def find(id):
        return Image.query.filter(Image.id == id).one_or_none()

    @staticmethod
    def find_by_ids(ids):
        images = Image.query.filter(Image.id.in_(ids)).all()
        image_dict = list_to_dict(images, "id")
        ordered_images = []
        for id in ids:
            image = image_dict.get(id)
            if image:
                ordered_images.append(image)
        return ordered_images

    @staticmethod
    def find_by_path(path):
        return Image.query.filter(Image.path == path).one_or_none()

    def url(self):
        return os.path.join(os.getenv("SERVER_NAME"), self.path)
