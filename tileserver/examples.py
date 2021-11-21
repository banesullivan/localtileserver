import pathlib

from tileserver.run import TileServer


def get_data_path(name):
    dirname = pathlib.Path(__file__).parent
    return dirname / 'data' / name


def get_bluemarble(port: int = 0, debug: bool = False):
    path = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    return TileServer(path, port=port, debug=debug)


def get_virtualearth(port: int = 0, debug: bool = False):
    path = get_data_path("frmt_wms_virtualearth.xml")
    return TileServer(path, port=port, debug=debug)


def get_arcgis(port: int = 0, debug: bool = False):
    path = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
    return TileServer(path, port=port, debug=debug)


def get_elevation(port: int = 0, debug: bool = False):
    path = get_data_path("aws_elevation_tiles_prod.xml")
    return TileServer(path, port=port, debug=debug)
