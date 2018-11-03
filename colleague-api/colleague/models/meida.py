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
    uid = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    path = db.Column(db.String(255), unique=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    size = db.Column(db.Integer)
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

    @staticmethod
    def path_to_url(path, location=MediaLocation.AliyunOSS):
        if location == MediaLocation.AliyunOSS:
            return os.path.join(os.getenv("SERVER_NAME"), path)

    def to_dict(self):
        return {
            "id": Image.encode_id(self.id),
            "url": Image.path_to_url(self.path),
            "width": self.width,
            "height": self.height,
        }

    @staticmethod
    def encode_id(id):
        return encode_id("image" + str(id))

    @staticmethod
    def decode_id(id):
        return int(decode_id(id)[5:])
