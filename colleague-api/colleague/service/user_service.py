# -*- coding:utf-8 -*-

from colleague.models.endorsement import (
    EndorseComment, UserEndorse, Endorsement, EndorseType)
from colleague.models.user import (User)
from colleague.utils import st_raise_error, ErrorCode


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
        st_raise_error(ErrorCode.NON_EXIST_USER)
