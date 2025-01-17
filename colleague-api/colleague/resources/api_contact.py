# -*- coding:utf-8 -*-


from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.contact import ContactRequest
from colleague.models.user import User
from colleague.service import contact_service, rc_service
from colleague.utils import decode_id, st_raise_error, ErrorCode, timestamp_to_datetime
from . import compose_response


class ApiContacts(Resource):
    SIZE = 100

    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        last_timestamp = decode_id(args['cursor']) if args.get('cursor') else None
        last_update_date = timestamp_to_datetime(last_timestamp)
        contacts = contact_service.get_contacts(current_user.user.id, last_update_date, ApiContacts.SIZE)
        return compose_response(result=contacts)


class ApiContactRequest(Resource):
    @login_required
    def get(self):
        # 获取联系人请求列表
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        last_request_id = decode_id(args['cursor']) if args.get('cursor') else None
        requests = contact_service.get_contact_requests(current_user.user.id, last_request_id, 20)
        return compose_response(result=requests)

    @login_required
    def post(self):
        # 请求建立联系人关系
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('uidA', type=unicode, location='json', required=True)
        reqparser.add_argument('uidB', type=unicode, location='json', required=True)
        reqparser.add_argument('comment', type=unicode, location='json', required=False)
        args = reqparser.parse_args()
        uidA = int(decode_id(args['uidA']))
        uidB = int(decode_id(args['uidB']))
        if uidB == current_user.user.id:
            st_raise_error(ErrorCode.NOT_ALLOWED_ADD_SELF)
        result = ContactRequest.add(current_user.user.id, uidA, uidB, args.get('comment'))
        if result:
            if current_user.user.id == uidA:
                message = "{}请求添加你为联系人".format(current_user.user.user_name)
            else:
                userA = User.find(uidA)
                message = "{}给你推荐了{}".format(current_user.user.user_name, userA.user_name)
            rc_service.send_system_notification(rc_service.RCSystemUser.T100001,
                                                args['uidB'], message)
        return compose_response(message="请求发送成功")

    @login_required
    def put(self):
        # 接受或者删除联系人申请
        # TODO: We need check whether two users were once in the same company?
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('id', type=unicode, location='json', required=True)
        reqparser.add_argument('accept', type=bool, location='json', required=True)
        args = reqparser.parse_args()
        id = decode_id(args["id"])
        result = contact_service.accept_contact_request(id, current_user.user.id, args["accept"])
        return compose_response(result=result)