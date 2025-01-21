import requests

from localtileserver.web.application import run_app


def test_home_page_with_file(bahamas):
    r = requests.get(bahamas.server_base_url)
    r.raise_for_status()


def test_home_page(flask_client):
    r = flask_client.get("/")
    assert r.status_code == 200
    r = flask_client.get("/?filename=foobar")
    assert r.status_code == 404


def test_cesium_split_view(flask_client):
    filenameA = "https://github.com/giswqs/data/raw/main/raster/landsat7.tif"
    filenameB = filenameA
    r = flask_client.get(f"/split/?filenameA={filenameA}&filenameB={filenameB}")
    assert r.status_code == 200
    r = flask_client.get(f"/split/?filenameA={filenameA}")
    assert r.status_code == 404
    r = flask_client.get(f"/split/?filenameB={filenameB}")
    assert r.status_code == 404
    r = flask_client.get("/split/form/")
    assert r.status_code == 200


def test_style(flask_client):
    r = flask_client.get("/api/thumbnail.png?colormap=viridis&indexes=1")
    assert r.status_code == 200


def test_list_palettes(flask_client):
    r = flask_client.get("/api/palettes")
    assert r.status_code == 200


def test_cog_validate_endpoint(flask_client, remote_file_url):
    r = flask_client.get(f"/api/validate?filename={remote_file_url}")
    assert r.status_code == 200


def test_run_app():
    app = run_app("bahamas", browser=False, run=False)
    with app.test_client() as f_client:
        r = f_client.get("/api/palettes")
        assert r.status_code == 200
