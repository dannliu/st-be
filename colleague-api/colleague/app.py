# -*- coding: utf-8 -*-

from flask import current_app, Flask
from flask_restful import Api
from werkzeug.exceptions import NotFound

from .utils import ApiException
from .config import settings
from .extensions import db, jwt


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
    from .api import TestUser
    from .api import Register, Verification

    api = Api(app)

    api.add_resource(Register, '/register')
    api.add_resource(TestUser, '/test')
    api.add_resource(Verification, '/send_verification')


def register_errorhandlers(app):
    return None


app = create_app(settings=settings)

if __name__ == '__main__':
    app.run(debug=True)
