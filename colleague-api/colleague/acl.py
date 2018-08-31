from functools import wraps

from flask_jwt_extended import verify_jwt_in_request

from colleague.extensions import jwt
from colleague.models import User


class UserObject(object):
    def __init__(self, **kwargs):
        self.user = User.find_user(kwargs.get('user_id'))
        self.device_id = kwargs.get("device_id")

        # TODO: other attributes


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    user_object = UserObject(**identity)
    if user_object.user is None \
            or not user_object.user.verify_token_metadata(identity, user_object.device_id):
        return None
    return user_object


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        # TODO: add check
        return fn(*args, **kwargs)
    return wrapper