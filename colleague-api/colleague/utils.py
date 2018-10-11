# -*- coding: utf-8 -*-
import base64
import hashlib
import random

import arrow

from Crypto.Cipher import AES

from colleague.extensions import redis_conn
from colleague.config import settings


class STError(object):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class ErrorCode(object):
    USER_NOT_EXIST = STError(2000, "用户不存在")
    NOT_REGISTERED = STError(2001, "还没有注册，快去注册吧")

    VERIFICATION_CODE_EXPIRE = STError(2002, '验证码已过期')
    VERIFICATION_CODE_NOT_MATCH = STError(2003, '验证码错误')
    VERIFICATION_CODE_MAX_REQUEST = STError(2004, '验证码请求过于频繁，请稍后再试')
    VERIFICATION_CODE_SEND_FAILED = STError(2005, '验证码发送失败，请稍后重试')

    USER_PASSWORD_WRONG = STError(2005, "用户名或者密码错误")
    DEVICE_MISMATCH = STError(2006, "用户登录设备发生变化")
    USER_UNAVAILABLE = STError(2007, '用户已被禁止访问')

    ALREADY_EXIST_MOBILE = STError(2008, '该手机号已被注册')
    ALREADY_EXIST_COLLEAGUE_ID = STError(2009, '该id已被注册，换一个新的吧')
    COLLEAGUE_ID_ALREADY_SET = STError(2010, '同事号只能设置一次')

    COMPANY_INFO_MISSED = STError(2010, "请填写正确的公司信息")
    WORK_EXPERIENCE_NOT_EXIST = STError(2011, "工作经历不存在")
    WORK_EXPERIENCE_CAN_NOT_BE_EXTINCT = STError(2012, "至少需要保留一条工作经历")
    RELATIONSHIP_ALREADY_CONNECTED = STError(2012, "已经是联系人了")
    ADD_RELATIONSHIP_NOT_COMMON_COMPANY = STError(2013, "只能添加你的同事")
    NOT_ALLOWED_ADD_SELF = STError(2013, "不能添加自己为好友")
    ENDORSE_TYPE_INVALID = STError(2014, "你要背的书我们还没有提供哦")


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


def decode_id(cursor):
    if cursor is None:
        return None
    if isinstance(cursor, unicode):
        cursor = cursor.encode('utf-8')
    cursor += '=' * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode(cursor)
    obj = AES.new(settings['AES_KEY'], AES.MODE_CBC, settings['AES_IV'])
    data = obj.decrypt(raw)
    return data.rstrip('\t')


def encode_id(cursor):
    if cursor is None:
        return None
    if isinstance(cursor, unicode):
        cursor = cursor.encode('utf-8')
    else:
        cursor = str(cursor)
    left = len(cursor) % 16
    left = 0 if left == 0 else (16 - left)
    data = cursor + '\t' * left
    obj = AES.new(settings['AES_KEY'], AES.MODE_CBC, settings['AES_IV'])
    return base64.urlsafe_b64encode(obj.encrypt(data)).rstrip('==')


def datetime_to_timestamp(dt):
    t = arrow.get(dt)
    return t.timestamp + t.microsecond / 1000000.0


def timestamp_to_str(timestamp):
    # use str will round the float point to 2
    return "{:.6f}".format(timestamp)


def timestamp_to_datetime(timestamp):
    return arrow.get(timestamp).naive


def list_to_dict(objects, key):
    dict_objects = {}
    for object in objects:
        dict_objects[getattr(object, key)] = object
    return dict_objects


def generate_random_verification_code():
    nums = []
    for i in range(6):
        nums.append(str(random.randint(0, 9)))
    return "".join(nums)
