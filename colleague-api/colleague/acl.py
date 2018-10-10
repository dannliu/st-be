from functools import wraps

from flask import request
from flask_jwt_extended import current_user
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended import verify_jwt_refresh_token_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError

from colleague.extensions import jwt
from colleague.models.user import User
from colleague.utils import decode_id


class UserObject(object):
    def __init__(self, **kwargs):
        self.user = User.find(decode_id(kwargs.get('user_id')))
        self.device_id = kwargs.get("device_id")
        # TODO: other attributes


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    user_object = UserObject(**identity)

    # TODO: raise different error
    if user_object.user is None \
            or user_object.user.is_logged_out() \
            or not user_object.user.is_available() \
            or not user_object.user.verify_token_metadata(identity, user_object.device_id):
        return None
    return user_object


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        check_token_device()
        # TODO: add check
        return fn(*args, **kwargs)

    return wrapper


def refresh_token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_refresh_token_in_request()
        check_token_device()
        return fn(*args, **kwargs)

    return wrapper


def check_token_device():
    device_id = request.headers.get("device-id")
    if not device_id or device_id != current_user.device_id:
        raise NoAuthorizationError("the device mismatches")
