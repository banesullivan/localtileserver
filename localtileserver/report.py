"""Environment and dependency reporting for localtileserver."""

import scooby


class Report(scooby.Report):
    """
    Generate a report on the dependencies of localtileserver.
    """

    def __init__(self, additional=None, ncol=3, text_width=80, sort=False):
        """
        Generate a report on the dependencies of localtileserver in this environment.
        """

        # Mandatory packages.
        core = [
            "localtileserver",
            *sorted(
                [
                    "click",
                    "fastapi",
                    "jinja2",
                    "numpy",
                    "rasterio",
                    "requests",
                    "rio_cogeo",
                    "rio_tiler",
                    "scooby",
                    "server_thread",
                    "uvicorn",
                ]
            ),
        ]

        # Optional packages.
        optional = sorted(
            [
                "cmocean",
                "colorcet",
                "folium",
                "ipyleaflet",
                "jupyter_server_proxy",
                "matplotlib",
                "rioxarray",
                "shapely",
                "xarray",
            ]
        )

        scooby.Report.__init__(
            self,
            additional=additional,
            core=core,
            optional=optional,
            ncol=ncol,
            text_width=text_width,
            sort=sort,
        )
