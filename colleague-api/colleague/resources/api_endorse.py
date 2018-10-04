# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.endorsement import UserEndorse, EndorseType, EndorseComment
from colleague.service import user_service
from colleague.utils import decode_id
from . import compose_response


class ApiEndorseNiubility(Resource):
    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('status', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        status = args.get('status')
        UserEndorse.update(to_uid, current_user.user.id, EndorseType.Niubility, status)
        endorsement = user_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=endorsement)


class ApiEndorseReliability(Resource):
    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('status', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        status = args.get('status')
        UserEndorse.update(to_uid, current_user.user.id, EndorseType.Reliability, status)
        endorsement = user_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=endorsement)


class ApiEndorseComment(Resource):
    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('text', type=int, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        EndorseComment.update(to_uid, current_user.user.id, args.get('text'))
        endorsement = user_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=endorsement)
