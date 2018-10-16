# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.endorsement import UserEndorse, EndorseType, EndorseComment
from colleague.service import user_service, endorse_service
from colleague.utils import decode_id
from . import compose_response


class ApiEndorseNiubility(Resource):

    @login_required
    def get(self):
        """
            Get user list who thinks `uid` is niubility
        """
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='args', required=True)
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        uid = decode_id(args.get('uid'))
        cursor = args.get('cursor')
        cursor = int(decode_id(cursor)) if cursor is not None else None
        endorsements = endorse_service.get_user_endorse(uid, EndorseType.Niubility, cursor)
        return compose_response(result=endorsements)

    @login_required
    def post(self):
        """
        Update the niubility status for `uid`
        """
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('status', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        status = args.get('status')
        UserEndorse.update(to_uid, current_user.user.id, EndorseType.Niubility, status)
        # endorsement = endorse_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=user_service.get_user_profile(to_uid))


class ApiEndorseReliability(Resource):
    @login_required
    def get(self):
        """
            Get user list who thinks `uid` is reliability
        """
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='args', required=True)
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        uid = decode_id(args.get('uid'))
        cursor = args.get('cursor')
        cursor = decode_id(cursor) if cursor is not None else None
        endorsements = endorse_service.get_user_endorse(uid, EndorseType.Reliability, cursor)
        return compose_response(result=endorsements)

    @login_required
    def post(self):
        """
        Update the reliability status for `uid`
        """
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('status', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        status = args.get('status')
        UserEndorse.update(to_uid, current_user.user.id, EndorseType.Reliability, status)
        # endorsement = colleague.service.endorse_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=user_service.get_user_profile(to_uid))


class ApiEndorseComment(Resource):

    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='args', required=True)
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        uid = decode_id(args.get('uid'))
        cursor = args.get('cursor')
        cursor = int(decode_id(cursor)) if cursor is not None else None
        comments = endorse_service.get_endorse_comments(uid, cursor)
        return compose_response(result=comments)

    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uid', type=unicode, location='json', required=True)
        reqparser.add_argument('text', type=unicode, location='json', required=True)
        args = reqparser.parse_args()
        to_uid = decode_id(args.get('uid'))
        EndorseComment.update(to_uid, current_user.user.id, args.get('text'))
        # endorsement = colleague.service.endorse_service.get_user_endorsement(to_uid, current_user.user.id)
        return compose_response(result=user_service.get_user_profile(to_uid), message="评论成功")
