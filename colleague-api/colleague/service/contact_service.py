# -*- coding:utf-8 -*-

import arrow

from colleague.extensions import db
from colleague.models.contact import (ContactRequest, ContactRequestStatus, Contact)
from colleague.models.endorsement import Endorsement
from colleague.models.user import User
from colleague.utils import (list_to_dict, encode_id, datetime_to_timestamp,
                             timestamp_to_str)


def get_contacts(uid, last_update_date, size):
    contacts = Contact.find_by_cursor(uid, last_update_date, size)
    next_cursor = None
    has_more = False
    if len(contacts) == size:
        has_more = True
        update_timestamp = datetime_to_timestamp(contacts[-1].updated_at)
        next_cursor = encode_id(timestamp_to_str(update_timestamp))
    uids = set()
    for contact in contacts:
        uids.add(contact.uidA)
        uids.add(contact.uidB)
    users = User.find_by_ids(uids)
    dict_users = list_to_dict(users, "id")
    json_contacts = []
    for contact in contacts:
        uid = contact.uidA == uid and contact.uidB or contact.uidA
        user = dict_users.get(uid)
        if user:
            json_contacts.append({
                'id': encode_id(contact.id),
                'user': user.to_dict(),
                'type': contact.type,
                'update_date': datetime_to_timestamp(contact.updated_at)
            })
    return {
        "has_more": has_more,
        "next_cursor": next_cursor,
        "contacts": json_contacts
    }


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
            # Update the endorsement total contacts
            Endorsement.update_total_contacts_count(request.uidA, 1)
            Endorsement.update_total_contacts_count(request.uidB, 1)
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
