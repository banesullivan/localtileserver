import pathlib


def get_data_path(name):
    dirname = pathlib.Path(__file__).parent
    return dirname / name
