import json
from urllib.parse import quote

import requests

from localtileserver.tileserver.application import run_app


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
    style_encoded = quote(json.dumps(style))
    r = flask_client.get(f"/api/thumbnail.png?style={style_encoded}")
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


def test_cog_validate_endpoint(flask_client, remote_file_url):
    r = flask_client.get(f"/api/validate?filename={remote_file_url}")
    assert r.status_code == 200
    non_cog = "https://data.kitware.com/api/v1/file/60747d792fa25629b9a79565/download"
    r = flask_client.get(f"/api/validate?filename={non_cog}")
    assert r.status_code == 415


def test_run_app():
    app = run_app("bahamas", browser=False, run=False)
    with app.test_client() as f_client:
        r = f_client.get("/api/sources")
        assert r.status_code == 200
