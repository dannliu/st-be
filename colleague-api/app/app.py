# -*- coding: utf-8 -*-

from flask import Flask
from flask_restful import Api

from .config import settings
from .errors import APIException, handle_api_exception
from .models import db


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
    db.create_all()
    app.db = db


def register_blueprints(app):
    from .api import TestUser
    from .api import Login

    api = Api(app)
    api.add_resource(TestUser, '/test')
    api.add_resource(Login, '/sns/v1/login')


def register_errorhandlers(app):
    app.register_error_handler(APIException, handle_api_exception)


app = create_app(settings=settings)

if __name__ == '__main__':
    app.run(debug=True)
