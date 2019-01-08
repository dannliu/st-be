# -*- coding: utf-8 -*-
import datetime
import os

import dotenv
from confire import Configuration

#dotenv.load_dotenv(dotenv.find_dotenv(".env", raise_error_if_not_found=True, usecwd=True))


class Config(Configuration):
    debug = False
    testing = False

    secret_key = os.getenv('SECRET_KEY')

    aes_key = os.getenv("AES_KEY")
    aes_iv = os.getenv("AES_IV")

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    sqlalchemy_database_uri = 'postgresql://{}:{}@{}:{}/{}'.format(
            db_user, db_pass, db_host, db_port, db_name
    )

    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT'))
    redis_db = int(os.getenv('REDIS_DB'))
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    jwt_access_token_expires = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES"))
    jwt_refresh_token_expires = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES"))

    max_verification_code_request_count = 5

    server_name = os.getenv("SERVER_NAME")
    upload_folder = os.getenv("UPLOAD_FOLDER")

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
            'AES_KEY': self.get('aes_key'),
            'AES_IV': self.get('aes_iv'),
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
