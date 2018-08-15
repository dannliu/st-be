# -*- coding: utf-8 -*-

from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, nullable=False, unique=True, autoincrement=True, primary_key=True)
    user_name = db.Column(db.String(256), nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def get_user(user_id):
        return User.find(user_id)