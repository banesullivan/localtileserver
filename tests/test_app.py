import requests


def test_home_page(bahamas):
    r = requests.get(bahamas.base_url)
    r.raise_for_status()
    r = requests.get(bahamas.create_url("roi"))
    r.raise_for_status()
