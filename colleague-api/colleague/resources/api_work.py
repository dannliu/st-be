# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user
from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models.work import WorkExperience, Organization
from colleague.utils import ErrorCode, st_raise_error, decode_id
from colleague.service import work_service


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

        company_id = args.get('company_id')
        company_name = args.get('company_name')
        if not company_id and not company_name:
            st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        if company_id:
            company = Organization.find_by_id(decode_id(company_id))
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        else:
            company = Organization.add(company_name)
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        work_experience = WorkExperience(uid=current_user.user.id,
                                         start_year=args['start_year'],
                                         start_month=args['start_month'],
                                         end_year=args['end_year'],
                                         end_month=args.get('end_month'),
                                         company_id=company.id,
                                         title=args['title'])
        WorkExperience.add(work_experience)
        return {
            'status': 200,
            'result': {"work_experiences": work_service.get_work_experiences(current_user.user.id)}
        }

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
        id = args.get('id')
        work_experience = WorkExperience.find_by_uid_id(current_user.user.id, decode_id(id))
        if not work_experience:
            st_raise_error(ErrorCode.WORK_EXPERIENCE_NOT_EXIST)

        company_id = args.get('company_id')
        company_name = args.get('company_name')
        if not company_id and not company_name:
            st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        if company_id:
            company = Organization.find_by_id(decode_id(company_id))
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        else:
            company = Organization.add(company_name)
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        work_experience.start_year = args['start_year']
        work_experience.start_month = args['start_month']
        work_experience.end_year = args['end_year']
        work_experience.end_month = args['end_month']
        work_experience.company_id = company.id
        work_experience.title = args['title']
        work_experience.update()
        return {
            'status': 200,
            'result': {"work_experiences": work_service.get_work_experiences(current_user.user.id)}
        }

    @login_required
    def delete(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('id', type=unicode, location='json', required=True)
        args = reqparser.parse_args()
        id = args.get('id')
        WorkExperience.delete(current_user.user.id, decode_id(id))
        return {
            'status': 200,
            'result': {"work_experiences": work_service.get_work_experiences(current_user.user.id)}
        }
