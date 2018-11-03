# -*- coding:utf-8 -*-

import hashlib
import os
from datetime import datetime

import imageio
from flask_restful import Resource, request
from flask_jwt_extended import current_user

from colleague.acl import login_required
from colleague.models.meida import Image, MediaLocation
from colleague.service.aliyun import aliyun_oss_service
from colleague.utils import st_raise_error, ErrorCode
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
            return compose_response(result=db_image.to_dict())
        img.seek(0)
        (result, request_id) = aliyun_oss_service.upload_file(saved_path, img)
        if result:
            height, width, channels = imageio.imread(data).shape
            db_image = Image(uid=current_user.user.id, path=saved_path,
                             width=width, height=height, size=len(data),
                             location=MediaLocation.AliyunOSS, info=request_id)
            Image.add(db_image)
            return compose_response(result=db_image.to_dict())
        else:
            st_raise_error(ErrorCode.UPLOAD_IMAGE_FAILED)
