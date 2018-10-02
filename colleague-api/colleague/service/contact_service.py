# -*- coding:utf-8 -*-

import arrow

from colleague.models.contact import (ContactRequest, ContactRequestStatus, Contact)
from colleague.models.user import User
from colleague.utils import list_to_dict, encode_id
from colleague.extensions import db


def get_contact_requests(uid, last_request_id, size):
    requests = ContactRequest.find_by_cursor(uid, last_request_id, size)
    _set_user_for_requests(requests)
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


# 这个方法其实是包含了 接受 和 删除
def accept_contact_request(id, uid, accept):
    request = ContactRequest.query.filter(ContactRequest.id == id,
                                          ContactRequest.uidB == uid).one_or_none()
    if request and request.status == ContactRequestStatus.Pending:
        request.status = ContactRequestStatus.Accepted if accept else ContactRequestStatus.Rejected
        request.end_at = arrow.utcnow().naive
        db.session.commit()
        if accept:
            Contact.add(request.uidA, request.uidB, request.type)
            _set_user_for_requests([request])
            return request.to_dict()


# I am not sure the efficient to use ForeignKey + Relation to connect user to request
def _set_user_for_requests(requests):
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
