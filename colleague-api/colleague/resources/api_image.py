# -*- coding:utf-8 -*-

from colleague.acl import login_required
from flask_restful import Resource


class ApiImage(Resource):
    @login_required
    def post():
        pass
