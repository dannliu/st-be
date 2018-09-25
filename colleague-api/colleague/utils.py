# -*- coding: utf-8 -*-
import hashlib

from colleague.extensions import redis_conn
import base64


class STError(object):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class ErrorCode(object):
    NON_EXIST_USER = 2001

    VERIFICATION_CODE_EXPIRE = 2002
    VERIFICATION_CODE_NOT_MATCH = 2003
    VERIFICATION_CODE_MAX_REQUEST = 2004

    USER_PASSWORD_WRONG = 2005
    DEVICE_MISMATCH = 2006
    USER_UNAVAILABLE = 2007

    ALREADY_EXIST_MOBILE = 2008
    ALREADY_EXIST_USER_ID = 2009

    COMPANY_INFO_MISSED = STError(2010, "请填写正确的公司信息")
    WORK_EXPERIENCE_NOT_EXIST = STError(2011, "工作经历不存在")


class ApiException(Exception):
    def __init__(self, status_code, error, http_status_code=200):
        self.status_code = status_code
        self.message = error
        self.http_status_code = http_status_code

    def to_dict(self):
        return {
            "status": self.status_code,
            "error": self.message  # TODO: change to display error
        }


def st_raise_error(error):
    raise ApiException(error.code, error.message)


class VerificationCode(object):
    def __init__(self, mobile):
        self.mobile = mobile

        self.count_key = "verification_count:{}".format(self.mobile)
        self.code_key = "verification_code:{}".format(self.mobile)

    def request_count(self):
        return int(redis_conn.get(self.count_key) or 0)

    def set_code(self, code):
        redis_conn.set(self.code_key, code, ex=10 * 60)

        redis_conn.incrby(self.count_key)
        redis_conn.expire(self.count_key, 24 * 60 * 60)

    def get_code(self):
        redis_conn.get(self.code_key)


def md5(secret, salt):
    h = hashlib.md5(secret.encode() + salt)
    return h.hexdigest()


def decode_cursor(cursor):
    if isinstance(cursor, unicode):
        cursor = cursor.encode('utf-8')
    return base64.urlsafe_b64decode(cursor)


def encode_cursor(cursor):
    return base64.urlsafe_b64encode(str(cursor))


def list_to_dict(objects, key):
    dict_objects = {}
    for object in objects:
        dict_objects[getattr(object, key)] = object
    return dict_objects
