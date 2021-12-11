import requests


def test_home_page_with_file(bahamas):
    r = requests.get(bahamas.base_url)
    r.raise_for_status()


def test_home_page(flask_client):
    r = flask_client.get("/")
    assert r
    r = flask_client.get("/roi/")
    assert r
