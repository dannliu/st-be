# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user

from colleague.models.work import WorkExperience, Organization
from colleague.utils import st_raise_error, ErrorCode


def get_work_experiences(uid):
    return [we.to_dict() for we in _get_work_experiences(uid)]


def _get_work_experiences(uid):
    def cmp(w1, w2):
        f1 = w1.end_year * 100 + (w1.end_month or 1)
        f2 = w2.end_year * 100 + (w2.end_month or 1)
        if f1 == f2:
            return (w1.update_date > w2.update_date) and -1 or 1
        else:
            return (f1 - f2) > 0 and -1 or 1

    # TODO we may need a service layer for this kind of api
    # TODO where do we handle the redis cache?
    work_experiences = WorkExperience.find_all_for_user(uid)
    work_experiences.sort(cmp=cmp)
    return work_experiences


def _get_or_add_company(company_id, company_name):
    """

    :param company_id:
    :param company_name:
    :return:
    """
    if not company_id and not company_name:
        return
    if company_id:
        company = Organization.find(company_id)
    else:
        company = Organization.find_by_name(company_name)
        if not company:
            company = Organization(name=company_name, verified=False)
            Organization.add(company)
    return company


def _update_user_title(uid):
    work_experiences = _get_work_experiences(uid)
    if len(work_experiences) > 0:
        latest = work_experiences[0]
        current_user.user.update_title(latest.company_id, latest.title)


def add_work_experience(uid, company_id, company_name, title, start_year,
                        start_month, end_year, end_month):
    company = _get_or_add_company(company_id, company_name)
    if company is None:
        st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
    work_experience = WorkExperience(uid=uid,
                                     company_id=company.id,
                                     title=title,
                                     start_year=start_year,
                                     start_month=start_month,
                                     end_year=end_year,
                                     end_month=end_month)
    WorkExperience.add(work_experience)
    _update_user_title(uid)


def update_work_experience(uid, id, company_id, company_name, title, start_year, start_month,
                           end_year, end_month):
    company = _get_or_add_company(company_id, company_name)
    if company is None:
        st_raise_error(ErrorCode.COMPANY_INFO_MISSED)
    work_experience = WorkExperience.find_by_uid_id(uid, id)
    if not work_experience:
        st_raise_error(ErrorCode.WORK_EXPERIENCE_NOT_EXIST)
    work_experience.start_year = start_year
    work_experience.start_month = start_month
    work_experience.end_year = end_year
    work_experience.end_month = end_month
    work_experience.company_id = company.id
    work_experience.title = title
    work_experience.update()
    _update_user_title(uid)


def delete_work_experience(uid, id):
    WorkExperience.delete(uid, id)
    _update_user_title(uid)


def search_company(keyword, count=10):
    if not keyword:
        return []
    striped_keyword = keyword.strip()
    if len(striped_keyword) == 0:
        return []
    companies = Organization.like(striped_keyword, count)
    return [_.to_dict() for _ in companies]
