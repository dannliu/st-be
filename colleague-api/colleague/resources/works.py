# -*- coding:utf-8 -*-

from flask_restful import Resource, reqparse

from colleague.acl import login_required
from colleague.models import WorkExperience, Organization
from flask_jwt_extended import current_user
from colleague.utils import ErrorCode, st_raise_error


class ApiWorkExperience(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        # company_id and company_name must have one
        # if the compnay is a new one, create a compnay record first
        self.reqparse.add_argument('company_id', type=str, location='json', required=False)
        self.reqparse.add_argument('company_name', type=str, location='json', required=False)
        self.reqparse.add_argument('title', type=str, location='json', required=True)
        self.reqparse.add_argument('start_year', type=int, location='json', required=True)
        self.reqparse.add_argument('start_month', type=int, location='json', required=True)
        # 2999 stands for present
        self.reqparse.add_argument('end_year', type=int, location='json', required=True)
        self.reqparse.add_argument('end_month', type=int, location='json', required=False)

    @login_required
    def post(self):
        # Add a new work expierence
        args = self.reqparse.parse_args()
        company_id = args.get('company_id')
        company_name = args.get('company_name')
        if not company_id or not company_name:
            st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        if company_id:
            company = Organization.find_by_id(company_id)
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        else:
            company = Organization.add(company_name)
            if not company:
                st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
        work_expierence = WorkExperience(uid=current_user.user.id,
                                         start_year=args['start_year'],
                                         start_month=args['start_month'],
                                         end_year=args['end_year'],
                                         end_month=args.get('end_month'),
                                         title=args['title'])
        WorkExperience.add(work_expierence)
        json_work_expierence = work_expierence.to_dict()
        json_work_expierence['company'] = company.to_dict()
        return {
            "status": 200,
            "result": json_work_expierence
        }