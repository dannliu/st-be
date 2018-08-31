# -*- coding: utf-8 -*-
from colleague.extensions import redis_conn


class ErrorCode(object):
    NON_EXIST_USER = 2001

    VERIFICATION_CODE_EXPIRE = 2002
    VERIFICATION_CODE_NOT_MATCH = 2003
    VERIFICATION_CODE_MAX_REQUEST = 2004

    USER_PASSWORD_WRONG = 2005
    DEVICE_MISMATCH = 2006


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


class VerificationCode(object):
    def __init__(self, mobile):
        self.mobile = mobile

        self.count_key = "verification_count:{}".format(self.mobile)
        self.code_key = "verification_code:{}".format(self.mobile)

    def request_count(self):
        return int(redis_conn.get(self.count_key) or 0)

    def set_code(self, code):
        redis_conn.set(self.count_key, code, ex=10 * 60)

        redis_conn.incrby(self.count_key)
        redis_conn.expire(self.count_key, 24 * 60 * 60)

    def get_code(self):
        redis_conn.get(self.count_key)