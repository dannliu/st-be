# -*- coding:utf-8 -*-


from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.user import Relationship, UserRelationshipRequest
from flask_jwt_extended import current_user
from colleague.utils import encode_cursor


class ContactList(Resource):
    SIZE = 10

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('cursor', type=unicode, location='args', required=False)

    @login_required
    def get(self):
        args = self.reqparse.parse_args()
        # todo: Need to add endorsement information from to_user
        contacts = Relationship.get_by_cursor(current_user.user.user_id, args.get('cursor'), ContactList.SIZE)
        next_cursor = None
        if contacts:
            next_cursor = encode_cursor(contacts[-1].get('update_at'))
        return {
            'status': 200,
            'result': {
                'next_cursor': next_cursor,
                'contacts': contacts
            }
        }


class RelationshipRequest(Resource):
    @login_required
    def get(self):
        user_id = current_user.user.user_id
        return {
            "status": 200,
            "results": UserRelationshipRequest.get_pending_requests(user_id)
        }

    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('user_requester_id', type=int, location='json', required=True)
        reqparser.add_argument('user_recommending_id', type=int, location='json', required=True)
        reqparser.add_argument('user_being_recommended_id', type=int, location='json', required=True)
        args = reqparser.parse_args()

        requester = UserRelationshipRequest.add(**args)

        return {
            "status": 200,
            "result": requester
        }

    @login_required
    def put(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('request_id', type=int, location='json', required=True)
        reqparser.add_argument('accept', type=bool, location='json', required=True)
        args = reqparser.parse_args()

        UserRelationshipRequest.complete(args["request_id"], args["accept"])

        return {
            "status": 200
        }
