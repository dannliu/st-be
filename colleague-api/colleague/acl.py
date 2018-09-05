from functools import wraps

from flask_jwt_extended import current_user
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended import verify_jwt_refresh_token_in_request
from flask_restful import reqparse

from colleague.extensions import jwt
from colleague.models import User
from colleague.utils import ApiException, ErrorCode


class UserObject(object):
    def __init__(self, **kwargs):
        self.user = User.find_user(kwargs.get('user_id'))
        self.device_id = kwargs.get("device_id")

        # TODO: other attributes


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    user_object = UserObject(**identity)
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
        check_token_device(args[0])
        # TODO: add check
        return fn(*args, **kwargs)

    return wrapper


def refresh_token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_refresh_token_in_request()
        check_token_device(args[0])
        return fn(*args, **kwargs)

    return wrapper


def check_token_device(resource):
    resource.reqparse = reqparse.RequestParser()
    resource.reqparse.add_argument('device-id', dest='device_id', type=str,
                                   location='headers', required=True)
    req_args = resource.reqparse.parse_args()
    device_id = req_args['device_id']
    if device_id != current_user.device_id:
        raise ApiException(ErrorCode.DEVICE_MISMATCH,
                           "the device mismatches")
