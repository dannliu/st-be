# -*- coding:utf-8 -*-


from flask_restful import Resource, reqparse
from flask_jwt_extended import current_user

from colleague.acl import login_required
from colleague.models.relationship import Relationship, RelationshipRequest
from colleague.utils import encode_id, decode_id, st_raise_error, ErrorCode
from colleague.service.relationship_service import get_relationship_requests
from . import compose_response


class ApiContacts(Resource):
    SIZE = 10

    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        # todo: Need to add endorsement information from to_user
        contacts = Relationship.get_by_cursor(current_user.user.user_id, args.get('cursor'), ApiContacts.SIZE)
        next_cursor = None
        if contacts:
            next_cursor = encode_id(contacts[-1].get('update_at'))
        return {
            'status': 200,
            'result': {
                'next_cursor': next_cursor,
                'contacts': contacts
            }
        }


class ApiRelationshipRequest(Resource):
    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        last_request_id = decode_id(args['cursor']) if args.get('cursor') else None
        requests = get_relationship_requests(current_user.user.id, last_request_id, 20)
        return compose_response(result={"requests": requests})

    @login_required
    def put(self):
        # Request a new relationship
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uidA', type=unicode, location='json', required=True)
        reqparser.add_argument('uidB', type=unicode, location='json', required=True)
        args = reqparser.parse_args()
        uidA = int(decode_id(args['uidA']))
        uidB = int(decode_id(args['uidB']))
        if uidB == current_user.user.id:
            st_raise_error(ErrorCode.NOT_ALLOWED_ADD_SELF)
        request = RelationshipRequest.add(current_user.user.id, uidA, uidB)

        return compose_response(message="请求发送成功")

    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('id', type=unicode, location='json', required=True)
        reqparser.add_argument('accept', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        id = encode_id(args["id"])
        RelationshipRequest.complete(current_user.user.id, id, args["accept"])
        return {
            "status": 200
        }
