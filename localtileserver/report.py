import scooby


class Report(scooby.Report):
    def __init__(self, additional=None, ncol=3, text_width=80, sort=False):
        """Initiate a scooby.Report instance."""

        # Mandatory packages.
        large_image_core = [
            "large_image",
            "large_image_source_gdal",
            "cachetools",
            "PIL",
            "psutil",
            "numpy",
            "palettable",
            "pyproj",
            "osgeo.gdal",
        ]
        core = [
            "localtileserver",
            "flask",
            "flask_caching",
            "requests",
            "werkzeug",
            "click",
            "scooby",
        ] + large_image_core

        # Optional packages.
        optional = [
            "ipyleaflet",
            "shapely",
            "folium",
            "large_image_source_mapnik",
            "large_image_source_pil",
            "large_image_source_tiff",
            "large_image_converter",
            "tifftools",
            "psutil",
            "pyvips",
        ]

        scooby.Report.__init__(
            self,
            additional=additional,
            core=core,
            optional=optional,
            ncol=ncol,
            text_width=text_width,
            sort=sort,
        )
