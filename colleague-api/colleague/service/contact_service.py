# -*- coding:utf-8 -*-

from colleague.models.contact import ContactRequest
from colleague.models.user import User
from colleague.utils import list_to_dict, encode_id


def get_contact_requests(uid, last_request_id, size):
    requests = ContactRequest.find_by_cursor(uid, last_request_id, size)
    uids = set()
    for request in requests:
        uids.add(request.uid)
        uids.add(request.uidA)
        uids.add(request.uidB)
    users = User.find_by_ids(uids)
    dict_users = list_to_dict(users, "id")
    for request in requests:
        user = dict_users.get(request.uid)
        userA = dict_users.get(request.uidA)
        userB = dict_users.get(request.uidB)
        if user and userA and userB:
            request.user = user
            request.userA = userA
            request.userB = userB
    next_cursor = None
    has_more = False
    if len(requests) == size:
        next_cursor = encode_id(requests[-1].id)
        has_next = True
    return {
        "next_cursor": next_cursor,
        "has_more": has_more,
        "requests": [_.to_dict() for _ in requests]
    }