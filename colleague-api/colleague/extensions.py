# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy

from .config import settings

db = SQLAlchemy()

import redis
redis_conn = redis.client.StrictRedis(host=settings['REDIS_HOST'], port=int(settings['REDIS_PORT']), db=settings['REDIS_DB'])


from flask_jwt_extended import JWTManager
jwt = JWTManager()