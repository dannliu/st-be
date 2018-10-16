# -*- coding:utf-8 -*-

import requests
import hashlib
import time
import os
import json
from colleague.utils import encode_id

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
