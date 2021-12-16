import pathlib


def get_data_path(name):
    dirname = pathlib.Path(__file__).parent
    return dirname / name


def get_pine_gulch_url():
    return "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"


def get_sf_bay_url():
    # https://data.kitware.com/#item/60747d792fa25629b9a79538
    return "https://data.kitware.com/api/v1/file/60747d792fa25629b9a79565/download"


def get_elevation_us_url():
    return "https://data.kitware.com/api/v1/file/5dbc4f66e3566bda4b4ed3af/download"
