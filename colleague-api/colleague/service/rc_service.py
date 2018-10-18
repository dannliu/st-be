# -*- coding:utf-8 -*-

import requests
import hashlib
import time
import os
import json
from colleague.utils import encode_id
from rongcloud import RongCloud


def get_rc_token(user):
    body = {
        'userId': encode_id(user.id),
        'name': user.user_name,
        'portraitUri': "http://39.107.239.252/2018/avatar/England-round.png"
    }
    app_key = os.getenv("RONG_KEY")
    app_sec = os.getenv("RONG_SEC")
    timestamp = int(time.time() * 1000)
    nonce = hashlib.md5(str(time.time())).hexdigest()
    v = "{}{}{}".format(app_sec, nonce, timestamp)
    sig = hashlib.sha1(v).hexdigest()
    headers = {
        'App-Key': app_key,
        'Timestamp': str(timestamp),
        "Nonce": nonce,
        "Signature": sig
    }
    resp = requests.post('https://api.cn.ronghub.com/user/getToken.json',
                         data=body, headers=headers)
    print resp.text
    if resp.status_code == 200:
        return json.loads(resp.text)["token"]
    else:
        return None


def refresh_user_info(user):
    rc = RongCloud(app_key=os.getenv("RONG_KEY"), app_secret=os.getenv("RONG_SEC"))
    rc.User.refresh(encode_id(user.id), user.user_name, user.avatar_url)


"""
100001: 有人请求你添加为好友
100002: 好友通过了你的请求
100003: 好友认为你是大牛
100004: 好友认为你很靠谱
100005: 好友给你做了评价
"""


class RCSystemUser(object):
    T100001 = "100001"
    T100002 = "100002"
    T100003 = "100003"
    T100004 = "100004"
    T100005 = "100005"


def send_system_notification(from_uid, to_uid, message):
    rc = RongCloud(app_key=os.getenv("RONG_KEY"), app_secret=os.getenv("RONG_SEC"))
    r = rc.Message.PublishSystem(
            fromUserId=from_uid,
            toUserId={to_uid},
            objectName='RC:TxtMsg',
            content=json.dumps({'content': message}),
            pushContent=message,
            pushData=json.dumps({'pushData': message}),
            isPersisted='0',
            isCounted='0')
    print r.status


def send_private_notification(from_uid, to_uid, message):
    rc = RongCloud(app_key=os.getenv("RONG_KEY"), app_secret=os.getenv("RONG_SEC"))
    r = rc.Message.publishPrivate(
            fromUserId=from_uid,
            toUserId={to_uid},
            objectName='RC:TxtMsg',
            content=json.dumps({'content': message, 'extra': 'new_contact'}),
            pushContent=message,
            pushData=json.dumps({'pushData': message}),
            isPersisted='0',
            isCounted='0')
    print r.status
