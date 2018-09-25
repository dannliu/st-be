# -*- coding:utf-8 -*-


from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.user import Relationships
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
        contacts = Relationships.get_by_cursor(current_user.user.user_id, args.get('cursor'), ContactList.SIZE)
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
