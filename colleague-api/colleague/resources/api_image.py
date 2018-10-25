# -*- coding:utf-8 -*-

from datetime import datetime
import os
import hashlib

from flask_restful import Resource, request

from colleague.acl import login_required
from colleague.service.aliyun import aliyun_oss_service
from colleague.utils import st_raise_error, ErrorCode, encode_id
from colleague.models.meida import Image, MediaLocation
from . import compose_response


class ApiImage(Resource):
    @login_required
    def post(self):
        img = request.files['image']
        date = datetime.now()
        saved_dir = "feed/{}/{}/{}".format(date.year, date.month, date.day)
        data = img.read()
        md5hash = hashlib.md5(data).hexdigest()
        saved_path = os.path.join(saved_dir, md5hash)
        db_image = Image.find_by_path(saved_path)
        if db_image:
            return compose_response(result={'id': encode_id(db_image.id)})
        img.seek(0)
        (result, request_id) = aliyun_oss_service.upload_file(saved_path, img)
        if result:
            db_image = Image(path=saved_path, location=MediaLocation.AliyunOSS,
                             info=request_id)
            Image.add(db_image)
            return compose_response(result={'id': encode_id(db_image.id)})
        else:
            st_raise_error(ErrorCode.UPLOAD_IMAGE_FAILED)
