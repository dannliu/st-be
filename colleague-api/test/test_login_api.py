import json
import time

import arrow
import flask_jwt_extended
import pytest
from flask import url_for

from colleague.models.user import User, UserStatus
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


def test_login_required_api_with_valid_access_token(client, user):
    access_token = get_token_by_login(client)[0]
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('testuser'), headers=headers)

    data = json.loads(rv.data)
    assert data["user"] == user.id


def test_login_required_api_with_valid_refresh_token(client, user):
    refresh_token = get_token_by_login(client)[1]
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(refresh_token)
    }
    rv = client.get(url_for('testuser'), headers=headers)

    assert rv.status_code == 422


def test_login_required_api_with_invalid_device(client, user):
    access_token = get_token_by_login(client)[0]
    headers = {
        'device-id': 'test-device-id2',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('testuser'), headers=headers)

    data = json.loads(rv.data)
    assert data["status"] == ErrorCode.DEVICE_MISMATCH.code


def test_login_required_api_with_regenerated_token(client, user):
    access_token1 = get_token_by_login(client)[0]
    time.sleep(1)
    access_token2 = get_token_by_login(client)[0]
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(access_token1)
    }
    rv1 = client.get(url_for('testuser'), headers=headers)
    assert rv1.status_code == 401

    headers['Authorization'] = 'Bearer {}'.format(access_token2)
    rv2 = client.get(url_for('testuser'), headers=headers)
    assert rv2.status_code == 200
    data = json.loads(rv2.data)
    assert data["user"] == user.id


def test_login_required_api_with_faked_token(client, user):
    access_token = get_token_by_login(client)[0]
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}111'.format(access_token)
    }
    rv1 = client.get(url_for('testuser'), headers=headers)
    assert rv1.status_code == 422


def test_refresh_token(client, user):
    access_token, refresh_token = get_token_by_login(client)
    time.sleep(1)
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(refresh_token)
    }
    rv = client.get(url_for('refreshtoken'), headers=headers)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    result = data['result']
    access_token2, refresh_token2 = result['access_token'], result['refresh_token']

    # assert previous access token and refresh token are invalid
    headers['Authorization'] = 'Bearer {}'.format(access_token)
    rv = client.get(url_for('testuser'), headers=headers)
    assert rv.status_code == 401
    headers['Authorization'] = 'Bearer {}'.format(refresh_token)
    rv = client.get(url_for('refreshtoken'), headers=headers)
    assert rv.status_code == 401

    # assert new access token is valid
    headers['Authorization'] = 'Bearer {}'.format(access_token2)
    rv = client.get(url_for('testuser'), headers=headers)
    data = json.loads(rv.data)
    assert data["user"] == user.id


def test_refresh_token_with_invalid_device(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id2',
        'Authorization': 'Bearer {}'.format(refresh_token)
    }
    rv = client.get(url_for('refreshtoken'), headers=headers)
    data = json.loads(rv.data)
    assert data["status"] == ErrorCode.DEVICE_MISMATCH.code


def test_refresh_token_with_valid_access_token(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('refreshtoken'), headers=headers)
    assert rv.status_code == 422


def test_refresh_token_with_faked_token(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}111'.format(refresh_token)
    }
    rv = client.get(url_for('refreshtoken'), headers=headers)
    assert rv.status_code == 422


def test_logout(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('logout'), headers=headers)
    data = json.loads(rv.data)
    assert data["status"] == 200
    assert user.status == UserStatus.Logout

    # assert access token and refresh token are invalid
    headers['Authorization'] = 'Bearer {}'.format(access_token)
    rv = client.get(url_for('testuser'), headers=headers)
    assert rv.status_code == 401
    headers['Authorization'] = 'Bearer {}'.format(refresh_token)
    rv = client.get(url_for('refreshtoken'), headers=headers)
    assert rv.status_code == 401


def test_logout_and_then_login(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('logout'), headers=headers)
    data = json.loads(rv.data)
    assert data["status"] == 200

    time.sleep(1)
    access_token2, refresh_token2 = get_token_by_login(client)
    headers['Authorization'] = 'Bearer {}'.format(access_token2)
    rv = client.get(url_for('testuser'), headers=headers)
    data = json.loads(rv.data)
    assert data["user"] == user.id
    assert user.status == UserStatus.Confirmed


def test_logout_with_invalid_device(client, user):
    access_token, refresh_token = get_token_by_login(client)
    headers = {
        'device-id': 'test-device-id2',
        'Authorization': 'Bearer {}'.format(access_token)
    }
    rv = client.get(url_for('logout'), headers=headers)
    data = json.loads(rv.data)
    assert data["status"] == ErrorCode.DEVICE_MISMATCH.code

    # assert access token is still valid
    headers['device-id'] = 'test-device-id'
    rv = client.get(url_for('testuser'), headers=headers)
    data = json.loads(rv.data)
    assert data["user"] == user.id


def get_token_by_login(client):
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
    return result['access_token'], result['refresh_token']
