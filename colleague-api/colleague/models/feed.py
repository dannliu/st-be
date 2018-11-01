# -*- coding:utf-8 -*-

from datetime import datetime
import os

from colleague.extensions import db
from colleague.utils import encode_id, datetime_to_timestamp


class FeedType(object):
    Default = 0  # moments


class Feed(db.Model):
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("colleague.models.user.User", lazy="selectin")
    type = db.Column(db.SMALLINT, nullable=False, default=0)
    images = db.Column(db.JSON, nullable=False)
    text = db.Column(db.TEXT, nullable=False)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def find_by_cursor(last_id, size):
        if last_id:
            feeds = Feed.query \
                .filter(Feed.id < last_id) \
                .order_by(db.desc(Feed.id)).offset(0).limit(size).all()
        else:
            feeds = Feed.query \
                .order_by(db.desc(Feed.id)).offset(0).limit(size).all()
        return feeds

    @staticmethod
    def find(id):
        return Feed.query.filter(Feed.id == id).one_or_none()

    @staticmethod
    def add(obj):
        db.session.add(obj)
        db.session.commit()

    def to_dict(self):
        return {
            'id': encode_id(self.id),
            'user': self.user.to_dict(),
            'type': self.type,
            'images': [os.path.join(os.getenv("SERVER_NAME"), url) for url in self.images],
            'text': self.text,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'create_at': datetime_to_timestamp(self.create_at)
        }


class FeedLikeStatus(object):
    Liked = 1
    UnLiked = 0

    @staticmethod
    def reverse(status):
        if status == FeedLikeStatus.Liked:
            return FeedLikeStatus.UnLiked
        else:
            return FeedLikeStatus.Liked


class FeedLike(db.Model):
    id = db.Column(db.BigInteger, nullable=False, unique=True, autoincrement=True, primary_key=True)
    uid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    feed_id = db.Column(db.BigInteger, db.ForeignKey('feed.id'), nullable=False)
    status = db.Column(db.SMALLINT, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    db.UniqueConstraint(uid, feed_id)

    def update():
        db.session.commit()

    @staticmethod
    def find_by_uid(uid, feed_id):
        return FeedLike.query \
            .filter(FeedLike.uid == uid, FeedLike.feed_id == feed_id) \
            .one_or_none()

    @staticmethod
    def add(obj):
        db.session.add(obj)
        db.session.commit()
