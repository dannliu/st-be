# -*- coding: utf-8 -*-
import datetime
import os
import dotenv

from confire import Configuration, environ_setting


dotenv.load_dotenv(dotenv.find_dotenv(".env", raise_error_if_not_found=True, usecwd=True))


class Config(Configuration):
    debug = False
    testing = False

    secret_key = environ_setting('SECRET_KEY', required=True)

    db_host = environ_setting("DB_HOST")
    db_port = environ_setting("DB_PORT", 5432, required=False)
    db_name = environ_setting("DB_NAME", required=True)
    db_user = environ_setting("DB_USER")
    db_pass = environ_setting("DB_PASS", "", required=False)
    sqlalchemy_database_uri = 'postgresql://{}:{}@{}:{}/{}'.format(
        db_user, db_pass, db_host, db_port, db_name
    )

    redis_host = environ_setting('REDIS_HOST', required=True)
    redis_port = int(environ_setting('REDIS_PORT', 6379, required=False))

    jwt_secret_key = environ_setting("JWT_SECRET_KEY", required=True)
    jwt_access_token_expires = int(environ_setting("JWT_ACCESS_TOKEN_EXPIRES", default=30, required=False))   # days
    jwt_refresh_token_expires = int(environ_setting("JWT_REFRESH_TOKEN_EXPIRES", default=365, required=False))  # days

    max_verification_code_request_count = 5

    def config_for_flask(self):
        """
        UserWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be
        disabled by default in the future.  Set it to True to suppress this warning.
        """
        return {
            'DEBUG': self.get('DEBUG'),
            'TESTING': self.get('TESTING'),
            'SQLALCHEMY_DATABASE_URI': self.get('SQLALCHEMY_DATABASE_URI'),
            "SQLALCHEMY_ECHO": False,
            "SQLALCHEMY_TRACK_MODIFICATIONS": True,
            'SECRET_KEY': self.get('secret_key'),
            'JWT_SECRET_KEY': self.get('JWT_SECRET_KEY'),
            'BUNDLE_ERRORS': True,
            "JWT_ACCESS_TOKEN_EXPIRES": datetime.timedelta(days=self.get('JWT_ACCESS_TOKEN_EXPIRES')),
            "JWT_REFRESH_TOKEN_EXPIRES": datetime.timedelta(days=self.get('JWT_REFRESH_TOKEN_EXPIRES'))
        }


class TestConfig(Config):
    testing = True
    debug = True


api_env = os.environ.get('API_ENV', 'dev')
if api_env == 'testing':
    settings = TestConfig.load()
else:
    settings = Config.load()
