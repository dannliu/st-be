
import json

from flask import url_for


def test_user_api(client):

    rv = client.get(url_for('testuser'), query_string={"user": "test"})

    data = json.loads(rv.data)
    assert data["user"] == "test"