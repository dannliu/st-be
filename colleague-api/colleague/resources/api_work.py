# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.service import work_service, user_service
from colleague.utils import ErrorCode, st_raise_error, decode_id
from . import compose_response


class ApiCompanySearch(Resource):
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('keyword', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        companies = work_service.search_company(args.get('keyword'))
        return compose_response(result={'companies': companies})


class ApiWorkExperience(Resource):

    @login_required
    def get(self):
        return {
            'status': 200,
            'result': {"work_experiences": work_service.get_work_experiences(current_user.user.id)}
        }

    @login_required
    def put(self):
        # Add a new work experience
        reqparser = reqparse.RequestParser()
        # company_id and company_name must have one
        # if the company is a new one, create a company record first
        reqparser.add_argument('company_id', type=unicode, location='json', required=False)
        reqparser.add_argument('company_name', type=unicode, location='json', required=False)
        reqparser.add_argument('title', type=unicode, location='json', required=True)
        reqparser.add_argument('start_year', type=int, location='json', required=True)
        reqparser.add_argument('start_month', type=int, location='json', required=True)
        # 2999 stands for present
        reqparser.add_argument('end_year', type=int, location='json', required=True)
        reqparser.add_argument('end_month', type=int, location='json', required=False)
        args = reqparser.parse_args()

        company_id = decode_id(args.get('company_id'))
        work_service.add_work_experience(uid=current_user.user.id,
                                         company_id=company_id,
                                         company_name=args['company_name'],
                                         title=args['title'],
                                         start_year=args['start_year'],
                                         start_month=args['start_month'],
                                         end_year=args['end_year'],
                                         end_month=args.get('end_month'))
        return compose_response(result=user_service.get_login_user_profile(current_user.user.id))

    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('id', type=unicode, location='json', required=True)
        # company_id and company_name must have one
        # if the company is a new one, create a company record first
        reqparser.add_argument('company_id', type=unicode, location='json', required=False)
        reqparser.add_argument('company_name', type=unicode, location='json', required=False)
        reqparser.add_argument('title', type=unicode, location='json', required=True)
        reqparser.add_argument('start_year', type=int, location='json', required=True)
        reqparser.add_argument('start_month', type=int, location='json', required=True)
        # 2999 stands for present
        reqparser.add_argument('end_year', type=int, location='json', required=True)
        reqparser.add_argument('end_month', type=int, location='json', required=False)

        args = reqparser.parse_args()
        id = decode_id(args.get('id'))
        company_id = decode_id(args.get('company_id'))
        work_service.update_work_experience(current_user.user.id, id,
                                            company_id,
                                            args['company_name'],
                                            args['title'],
                                            args['start_year'],
                                            args['start_month'],
                                            args['end_year'],
                                            args['end_month'])
        return compose_response(result=user_service.get_login_user_profile(current_user.user.id))

    @login_required
    def delete(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('id', type=unicode, location='json', required=True)
        args = reqparser.parse_args()
        id = decode_id(args.get('id'))
        wks = work_service.get_work_experiences(current_user.user.id)
        if len(wks) <= 1:
            st_raise_error(ErrorCode.WORK_EXPERIENCE_CAN_NOT_BE_EXTINCT)
        work_service.delete_work_experience(current_user.user.id, id)
        return compose_response(result=user_service.get_login_user_profile(current_user.user.id))
