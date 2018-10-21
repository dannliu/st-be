# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user

from colleague.models.endorsement import EndorseComment
from colleague.models.user import User
from colleague.models.contact import Contact, ContactStatus
from colleague.service import work_service
from colleague.service.endorse_service import get_user_endorsement
from colleague.utils import st_raise_error, ErrorCode


def get_user_profile(uid, viewer_uid):
    """
    Get a user's profile. A views B's profile.
    uid = B's id, viewer_uid = A's id
    :param uid: Target user id
    :param viewer_uid: The viewer's uid.
    :return: Profile
    """
    user = User.find(uid)
    if not user:
        st_raise_error(ErrorCode.USER_NOT_EXIST)
    work_experiences = work_service.get_work_experiences(uid)
    endorsement = get_user_endorsement(uid, current_user.user.id)
    latest_comment = EndorseComment.find_latest_by_uid(uid)
    profile = user.to_dict()
    profile['endorsement'] = endorsement
    profile['work_experiences'] = work_experiences
    if latest_comment:
        profile['latest_comment'] = latest_comment.to_dict()
    contact = Contact.find_by_uid(uid, viewer_uid)
    profile['is_contact'] = contact is not None \
                            and contact.status == ContactStatus.Connected
    return profile


def get_login_user_profile(uid):
    """
    Get current login user's profile
    :param uid: Login user id
    :return: Profile (without latest_comment, endorsement)
    """
    # fetch the user info from db,
    # just in case the info has been updated somewhere
    json_user = User.find(uid).to_dict_with_mobile()
    json_user['work_experiences'] = work_service.get_work_experiences(uid)
    return json_user
