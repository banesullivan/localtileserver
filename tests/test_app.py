import base64
import json

import requests


def test_home_page_with_file(bahamas):
    r = requests.get(bahamas.server_base_url)
    r.raise_for_status()


def test_home_page(flask_client):
    r = flask_client.get("/")
    assert r.status_code == 200
    r = flask_client.get("/roi/")
    assert r.status_code == 200
    r = flask_client.get("/?filename=foobar")
    assert r.status_code == 404


def test_cesium_split_view(flask_client):
    filenameA = "https%3A%2F%2Fopendata.digitalglobe.com%2Fmarshall-fire21%2Fpre%2F13%2F031131113123%2F2021-12-21%2F1050010028D5F600-visual.tif"
    filenameB = "https%3A%2F%2Fopendata.digitalglobe.com%2Fmarshall-fire21%2Fpost-event%2F2021-12-30%2F10200100BCB1A500%2F10200100BCB1A500.tif"
    r = flask_client.get(f"/split/?filenameA={filenameA}&filenameB={filenameB}")
    assert r.status_code == 200
    r = flask_client.get(f"/split/?filenameA={filenameA}")
    assert r.status_code == 404
    r = flask_client.get(f"/split/?filenameB={filenameB}")
    assert r.status_code == 404
    r = flask_client.get("/split/form/")
    assert r.status_code == 200


def test_style_json(flask_client):
    style = {
        "bands": [
            {"band": 1, "palette": ["#000", "#0f0"]},
        ]
    }
    style_base64 = base64.urlsafe_b64encode(json.dumps(style).encode()).decode()
    r = flask_client.get(f"/api/thumbnail.png?style={style_base64}")
    assert r.status_code == 200
    # Test bad style
    bad_style = "foobar"
    r = flask_client.get(f"/api/thumbnail.png?style={bad_style}")
    assert r.status_code == 400


def test_list_palettes(flask_client):
    r = flask_client.get("/api/palettes")
    assert r.status_code == 200


def test_list_sources(flask_client):
    r = flask_client.get("/api/sources")
    assert r.status_code == 200
