import scooby


class Report(scooby.Report):
    def __init__(self, additional=None, ncol=3, text_width=80, sort=False):
        """Generate a report on the dependencies of localtileserver in this environment."""

        # Mandatory packages.
        core = ["localtileserver"] + sorted(
            [
                "rasterio",
                "rio_tiler",
                "numpy",
                "server_thread",
                "flask",
                "flask_caching",
                "flask_cors",
                "flask_restx",
                "rio_cogeo",
                "werkzeug",
                "click",
            ]
        )

        # Optional packages.
        optional = sorted(
            [
                "gunicorn",
                "ipyleaflet",
                "jupyterlab",
                "jupyter_server_proxy",
                "traitlets",
                "shapely",
                "folium",
                "matplotlib",
                "requests" "colorcet",
                "cmocean",
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
