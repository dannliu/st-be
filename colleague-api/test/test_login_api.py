import json

import arrow
import flask_jwt_extended
import pytest
from flask import url_for

from colleague.models import User, UserStatus
from colleague.utils import ErrorCode


@pytest.yield_fixture(scope='function')
def user(db):
    _user = User()
    _user.mobile = '12345678910'
    _user.hash_password('123456')
    _user.user_name = 'user_name1'
    _user.avatar = 'avatar1'
    _user.gender = 0
    _user.status = UserStatus.Confirmed
    db.session.add(_user)
    db.session.commit()

    yield _user
    db.session.delete(_user)
    db.session.commit()


def test_login(client, user):
    headers = {
        'content-type': 'application/json',
        'device-id': 'test-device-id'
    }
    data = {
        'mobile': '12345678910',
        'password': '123456'
    }
    rv = client.post(url_for('login'), headers=headers, data=json.dumps(data))
    assert rv.status_code == 200

    data = json.loads(rv.data)
    result = data['result']
    assert 'access_token' in result
    assert 'refresh_token' in result
    access_token = result['access_token']
    refresh_token = result['refresh_token']

    access_metadata = flask_jwt_extended.decode_token(access_token)
    access_identity = access_metadata['identity']
    assert access_identity.get('user_id', -1) == user.id
    assert access_identity.get('device_id', '') == 'test-device-id'
    assert access_identity.get('timestamp', -1) == arrow.get(user.last_login_at).timestamp
    assert access_metadata.get('type', '') == 'access'

    refresh_metadata = flask_jwt_extended.decode_token(refresh_token)
    refresh_identity = refresh_metadata['identity']
    assert refresh_identity == access_identity
    assert refresh_metadata.get('type', '') == 'refresh'


def test_login_with_wrong_pw(client, user):
    headers = {
        'content-type': 'application/json',
        'device-id': 'test-device-id'
    }
    data = {
        'mobile': '12345678910',
        'password': 'wrong'
    }
    rv = client.post(url_for('login'), headers=headers, data=json.dumps(data))
    assert rv.status_code == 200

    data = json.loads(rv.data)
    assert data.get('status', -1) == ErrorCode.USER_PASSWORD_WRONG


def test_login_with_wrong_mobile(client, user):
    headers = {
        'content-type': 'application/json',
        'device-id': 'test-device-id'
    }
    data = {
        'mobile': 'wrong',
        'password': '123456'
    }
    rv = client.post(url_for('login'), headers=headers, data=json.dumps(data))
    assert rv.status_code == 200

    data = json.loads(rv.data)
    assert data.get('status', -1) == ErrorCode.NON_EXIST_USER


def test_login_to_blocked_user(client, user, db):
    user.status = UserStatus.Blocked
    db.session.commit()

    headers = {
        'content-type': 'application/json',
        'device-id': 'test-device-id'
    }
    data = {
        'mobile': '12345678910',
        'password': '123456'
    }
    rv = client.post(url_for('login'), headers=headers, data=json.dumps(data))
    assert rv.status_code == 200

    data = json.loads(rv.data)
    assert data.get('status', -1) == ErrorCode.USER_UNAVAILABLE
