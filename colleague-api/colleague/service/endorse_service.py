# -*- coding:utf-8 -*-

from colleague.models.endorsement import UserEndorse, EndorseType, Endorsement, EndorseComment
from colleague.utils import (st_raise_error, ErrorCode, encode_id)
from . import cursor_data


def get_user_endorse(uid, type, latest_id, size=20):
    """
    Get endorse records.
    #TODO the api name
    :param uid: Target user
    :param type: Endorse type @see EndorseType
    :param latest_id: The latest id for already fetched list.
    :param size: records count
    :return: [UserEndorse]
    """
    if not EndorseType.check(type):
        st_raise_error(ErrorCode.ENDORSE_TYPE_INVALID)
    endorsements = UserEndorse.find_by_cursor(uid, type, latest_id, size)
    has_more = False
    next_cursor = None
    if len(endorsements) == size:
        has_more = True
        next_cursor = encode_id(endorsements[-1].id)
    json_endorsements = [item.to_dict() for item in endorsements]
    return cursor_data(has_more, next_cursor, 'endorsements', json_endorsements)


def get_endorse_comments(uid, latest_id, size=20):
    comments = EndorseComment.find_by_cursor(uid, latest_id, size)
    has_more = False
    next_cursor = None
    if len(comments) == size:
        has_more = True
        next_cursor = encode_id(comments[-1].id)
    json_comments = [item.to_dict() for item in comments]
    return cursor_data(has_more, next_cursor, 'comments', json_comments)


def get_user_endorsement(uid, from_uid):
    """
    Get the overall endorsement state
    :param uid: Target uid
    :param from_uid: Who endorse the target user
    :return: Overall endorsement state
    """
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
