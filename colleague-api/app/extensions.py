# -*- coding: utf-8 -*-

from .config import settings

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

import redis
redis_conn = redis.client.StrictRedis(host=settings['REDIS_HOST'], port=settings['REDIS_PORT'])
