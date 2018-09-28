# -*- coding: utf-8 -*-

from flask import current_app, Flask
from flask_jwt_extended.exceptions import JWTExtendedException
from flask_restful import Api
from werkzeug.exceptions import NotFound

from .utils import ApiException
from .config import settings
from .extensions import jwt
from colleague.models.user import db


class ColleagueApi(Api):
    @staticmethod
    def _ignore_exception(e, v, tb):
        if isinstance(v, NotFound):
            return True
        return False

    def handle_error(self, e):
        if isinstance(e, ApiException):
            current_app.logger.warning("{} %s".format(e.status_code), e.message)
            return self.make_response(e.to_dict(), e.http_status_code)
        if isinstance(e, JWTExtendedException):
            return self.make_response({"error": e.message}, 401)

        self.record_exception(e)
        return super(ColleagueApi, self).handle_error(e)

    def record_exception(self, e):
        current_app.logger.error(e)

    def record_and_reraise(self, e):
        """record this exception and propagate"""
        self.record_exception(e)
        raise e


def create_app(config_object=None, settings=None):
    """
    An application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/
    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    if settings:
        app.settings = settings
        app.config.update(settings.config_for_flask())

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)

    return app


def register_extensions(app):
    db.init_app(app)
    db.app = app
    app.db = db

    jwt.init_app(app)


def register_blueprints(app):
    from .resources.api_user import (Register, Verification, Login, RefreshToken, Logout, UserDetail, UploadUserIcon,
                                     SearchUsers)
    from .resources.api_work import ApiWorkExperience
    from .resources.api_relationship import ApiContacts, ApiRelationshipRequest

    api = ColleagueApi(app)

    api.add_resource(Register, '/register')
    api.add_resource(Verification, '/send_verification')
    api.add_resource(Login, '/login')
    api.add_resource(RefreshToken, '/refresh_token')
    api.add_resource(Logout, '/logout')
    api.add_resource(UserDetail, '/user_detail')
    api.add_resource(UploadUserIcon, '/upload_avatar')
    api.add_resource(SearchUsers, '/search/users')
    api.add_resource(ApiContacts, '/contacts')
    api.add_resource(ApiRelationshipRequest, '/contact_request')
    # Work related api
    api.add_resource(ApiWorkExperience, '/work_experience')


def register_errorhandlers(app):
    return None


app = create_app(settings=settings)

if __name__ == '__main__':
    app.run(debug=True)
