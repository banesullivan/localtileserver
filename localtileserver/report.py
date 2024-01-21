import scooby


class Report(scooby.Report):
    def __init__(self, additional=None, ncol=3, text_width=80, sort=False):
        """Generate a report on the dependencies of localtileserver in this environment."""

        # Mandatory packages.
        rio_tiler_core = [
            "rasterio",
            "rio_tiler",
            "numpy",
        ]
        core = [
            "localtileserver",
            "flask",
            "flask_caching",
            "flask_cors",
            "flask_restx",
            "requests",
            "rio_cogeo",
            "werkzeug",
            "click",
            "server_thread",
            "scooby",
        ] + rio_tiler_core

        # Optional packages.
        optional = [
            "gunicorn",
            "ipyleaflet",
            "jupyterlab",
            "jupyter_server_proxy",
            "traitlets",
            "shapely",
            "folium",
            "matplotlib",
            "colorcet",
            "cmocean",
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
