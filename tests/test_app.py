import requests

from localtileserver.web import create_app
from localtileserver.web.fastapi_app import run_app


def test_home_page_with_file(bahamas):
    r = requests.get(bahamas.server_base_url)
    r.raise_for_status()


def test_home_page(flask_client):
    r = flask_client.get("/")
    assert r.status_code == 200


def test_cesium_split_view(flask_client):
    r = flask_client.get("/split/form/")
    assert r.status_code == 200


def test_style(flask_client):
    r = flask_client.get("/api/thumbnail.png?colormap=viridis&indexes=1")
    assert r.status_code == 200


def test_list_palettes(flask_client):
    r = flask_client.get("/api/palettes")
    assert r.status_code == 200


def test_cog_validate_endpoint(flask_client, bahamas_file):
    r = flask_client.get(f"/api/validate?filename={bahamas_file}")
    assert r.status_code == 200


def test_run_app():
    from fastapi.testclient import TestClient

    app = run_app("bahamas", browser=False, run=False)
    with TestClient(app) as client:
        r = client.get("/api/palettes")
        assert r.status_code == 200


def test_cors_all_enabled():
    from fastapi.testclient import TestClient

    app = create_app(cors_all=True)
    with TestClient(app) as client:
        r = client.get("/api/palettes", headers={"Origin": "http://example.com"})
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == "*"


def test_cesium_viewer_invalid_filename(flask_client):
    r = flask_client.get("/?filename=/nonexistent/path/to/file.tif")
    assert r.status_code == 404


def test_cesium_split_viewer_invalid_filename(flask_client):
    r = flask_client.get("/split/?filenameA=/nonexistent/path/to/file.tif")
    assert r.status_code == 404
