# -*- coding:utf-8 -*-

from colleague.models.work import WorkExperience
from colleague.models.work import Organization


def get_work_experiences(uid):
    def cmp(w1, w2):
        f1 = w1.end_year + (w1.end_month or 1)
        f2 = w2.end_year + (w2.end_month or 1)
        if f1 == f2:
            return (w1.update_date > w2.update_date) and -1 or 1
        else:
            return (f1 - f2) > 0 and -1 or 1

    # TODO we may need a service layer for this kind of api
    # TODO where do we handle the redis cache?
    work_experiences = WorkExperience.find_all_for_user(uid)
    work_experiences.sort(cmp=cmp)
    return [we.to_dict() for we in work_experiences]


def search_company(keyword, count = 10):
    if not keyword:
        return []
    striped_keyword = keyword.strip()
    if len(striped_keyword) == 0:
        return []
    companies = Organization.like(striped_keyword, count)
    return [_.to_dict() for _ in companies]
