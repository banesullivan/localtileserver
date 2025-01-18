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
        return f"https://github.com/banesullivan/localtileserver/raw/main/localtileserver/tiler/data/{name}"
    else:
        return DIRECTORY / name


def get_sf_bay_url():
    return "https://localtileserver.s3.us-west-2.amazonaws.com/examples/TC_NG_SFBay_US_Geo_COG.tif"


def get_elevation_us_url():
    return "https://localtileserver.s3.us-west-2.amazonaws.com/examples/elevation_cog.tif"


def get_oam2_url():
    return "https://localtileserver.s3.us-west-2.amazonaws.com/examples/oam2.tif"


def convert_dropbox_url(url: str):
    return url.replace("https://www.dropbox.com", "https://dl.dropbox.com")


def clean_url(url: str):
    """Fix the download URL for common hosting services like dropbox."""
    return convert_dropbox_url(url)


def get_co_elevation_url():
    return "https://localtileserver.s3.us-west-2.amazonaws.com/examples/co_elevation.tif"
