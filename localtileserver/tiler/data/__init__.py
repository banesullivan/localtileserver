# flake8: noqa: W503
import os
import pathlib

DIRECTORY = pathlib.Path(__file__).parent


def str_to_bool(v):
    return v.lower() in ("yes", "true", "t", "1", "on", "y")


def get_building_docs():
    if "LOCALTILESERVER_BUILDING_DOCS" in os.environ and str_to_bool(
        os.environ["LOCALTILESERVER_BUILDING_DOCS"]
    ):
        return True
    return False


def get_data_path(name):
    if get_building_docs():
        return f"https://github.com/banesullivan/localtileserver/raw/main/localtileserver/tileserver/data/{name}"
    else:
        return DIRECTORY / name


def get_pine_gulch_url():
    return "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"


def get_sf_bay_url():
    # Non-COG: https://data.kitware.com/#item/60747d792fa25629b9a79538
    # COG: https://data.kitware.com/#item/626854a04acac99f42126a72
    return "https://data.kitware.com/api/v1/file/626854a14acac99f42126a74/download"


def get_elevation_us_url():
    return "https://data.kitware.com/api/v1/file/5dbc4f66e3566bda4b4ed3af/download"


def get_oam2_url():
    return "https://oin-hotosm.s3.amazonaws.com/59c66c5223c8440011d7b1e4/0/7ad397c0-bba2-4f98-a08a-931ec3a6e943.tif"


def convert_dropbox_url(url: str):
    return url.replace("https://www.dropbox.com", "https://dl.dropbox.com")


def clean_url(url: str):
    """Fix the download URL for common hosting services like dropbox."""
    return convert_dropbox_url(url)


def get_co_elevation_url():
    return "https://data.kitware.com/api/v1/file/62e4408fbddec9d0c4443918/download"
