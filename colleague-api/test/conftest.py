# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import os

import pytest
from sqlalchemy.exc import InternalError as SQLAInternalError

from colleague.app import create_app
from colleague.config import TestConfig
from colleague.extensions import db as _db


@pytest.yield_fixture(scope='function')
def app():
    _app = create_app(settings=TestConfig.load())

    ctx = _app.test_request_context()
    ctx.push()

    yield _app
    ctx.pop()


@pytest.yield_fixture(scope='function')
def db(app):
    _db.app = app
    _db.create_all()
    yield _db
    _db.session.remove()
    try:
        _db.drop_all()
    except SQLAInternalError:
        # could happen because SQLA issues "drop" without cascade
        pass

