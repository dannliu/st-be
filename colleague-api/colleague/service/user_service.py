# -*- coding:utf-8 -*-

from colleague.models.user import User, Endorsement

"""
class BasicUser(object):
    id,
    uid,
    name,
    avatar,
    title,
    company,
    endorsement,
"""


def get_basic_user(uid):
    user = User.find(uid)
    endorsement = Endorsement.find_by_uid(uid)
