import base64
import json

import requests


def test_home_page_with_file(bahamas):
    r = requests.get(bahamas.server_base_url)
    r.raise_for_status()


def test_home_page(flask_client):
    r = flask_client.get("/")
    assert r
    r = flask_client.get("/roi/")
    assert r


def test_style_json(flask_client):
    style = {
        "bands": [
            {"band": 1, "palette": ["#000", "#0f0"]},
        ]
    }
    style_base64 = base64.urlsafe_b64encode(json.dumps(style).encode()).decode()
    r = flask_client.get(f"/api/thumbnail.png?style={style_base64}")
    assert r.status_code == 200
