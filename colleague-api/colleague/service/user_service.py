# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user

from colleague.models.endorsement import (
    EndorseComment, UserEndorse, Endorsement, EndorseType)
from colleague.models.user import (User)
from colleague.models.endorsement import EndorseComment
from colleague.utils import st_raise_error, ErrorCode
from colleague.service import work_service


def get_user_endorsement(uid, from_uid):
    endorsement = Endorsement.find_by_uid(uid)
    if endorsement:
        json_endorsement = endorsement.to_dict()
        endorse_comment = EndorseComment.find_by_from_uid(uid, from_uid)
        if endorse_comment:
            json_endorsement['comment'] = endorse_comment.text
        endorse_niubility = UserEndorse.find_by_from_uid(uid, from_uid, EndorseType.Niubility)
        if endorse_niubility:
            json_endorsement['is_niubility'] = True
        endorse_reliability = UserEndorse.find_by_from_uid(uid, from_uid, EndorseType.Reliability)
        if endorse_reliability:
            json_endorsement['is_reliability'] = True
        return json_endorsement


def get_user_profile(uid):
    user = User.find(uid)
    if not user:
        st_raise_error(ErrorCode.USER_NOT_EXIST)
    work_experiences = work_service.get_work_experiences(uid)
    endorsement = get_user_endorsement(uid, current_user.user.id)
    latest_comment = EndorseComment.find_latest_by_uid(uid)
    json_user = user.to_dict()
    json_user['endorsement'] = endorsement
    json_user['work_experiences'] = work_experiences
    json_user['latest_comment'] = latest_comment.to_dict()
    return json_user
