# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user

from colleague.models.endorsement import EndorseComment
from colleague.models.user import User
from colleague.service import work_service
from colleague.service.endorse_service import get_user_endorsement
from colleague.utils import st_raise_error, ErrorCode


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
    if latest_comment:
        json_user['latest_comment'] = latest_comment.to_dict()
    return json_user


def get_login_user_profile(uid):
    # fetch the user info from db,
    # just in case the info has been updated somewhere
    json_user = User.find(uid).to_dict_with_mobile()
    json_user['work_experiences'] = work_service.get_work_experiences(uid)
    return json_user
