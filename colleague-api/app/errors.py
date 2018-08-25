from flask import jsonify


def handle_api_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class APIException(Exception):
    def __init__(self, http_status_code, code, error_message, result=None):
        Exception.__init__(self)
        self.status_code = http_status_code
        self.code = code
        self.error_message = error_message
        self.result = result

    def to_dict(self):
        rv = {'status': self.code,
              'error': self.error_message}
        if self.result:
            rv.update({
                'result': self.result
            })
        return rv


class APIErrors:
    """
    tuple(http_status_code, code, error_message)
    """

    # Authentication errors
    UNREGISTERED_USER = (401, 4011, 'Unregistered user')
    PASSWORD_INCORRECT = (401, 4012, 'Password is incorrect')
    TOKEN_EXPIRED = (401, 4013, 'Token is expired')
    TOKEN_INVALID = (401, 4014, 'Token is invalid')
