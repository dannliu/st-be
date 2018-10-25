# -*- coding:utf-8 -*-

import os

import oss2


def upload_file(path, file_stream):
    key = os.getenv("OSS_KEY")
    sec = os.getenv("OSS_SEC")
    bucket_name = os.getenv("OSS_BUCKET")
    endpoint = os.getenv("OSS_ENDPOINT")
    auth = oss2.Auth(key, sec)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    try:
        result = bucket.put_object(path, file_stream)
    except Exception, e:
        print e
    return result.status == 200
