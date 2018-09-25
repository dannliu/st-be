# -*- coding:utf-8 -*-

from colleague.models.work import WorkExperience
from flask_jwt_extended import current_user


def get_all_work_experiences():
    # todo we may need a server layer for this kind of api
    work_experiences = WorkExperience.find_all_for_user(current_user.user.id)
    work_experiences.sort(cmp=cmp)
    return [we.to_dict() for we in work_experiences]

    def cmp(w1, w2):
        f1 = w1.end_year + (w1.end_month or 1)
        f2 = w2.end_year + (w2.end_month or 1)
        if f1 == f2:
            return (w1.update_date > w2.update_date) and -1 or 1
        else:
            return (f1 - f2) > 0 and -1 or 1
