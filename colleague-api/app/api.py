# -*- coding: utf-8 -*-
import json
import re

from flask import request, current_app
from flask_restful import Resource, reqparse


class TestUser(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('user', type=str, location='args', required=True)

    def get(self):
        args = self.reqparse.parse_args()
        return {'user': args["user"]}
