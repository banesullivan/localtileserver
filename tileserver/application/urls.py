from werkzeug.routing import FloatConverter as BaseFloatConverter

from tileserver.application import app, rest, views


class FloatConverter(BaseFloatConverter):
    regex = r"-?\d+(\.\d+)?"


# URL Parsers
app.url_map.converters["float"] = FloatConverter

# Views/pages
app.add_url_rule("/", view_func=views.CesiumViewer.as_view("index"))
app.add_url_rule("/roi/", view_func=views.GeoJSViewer.as_view("roi"))

# REST endpoints
app.add_url_rule("/thumbnail", view_func=rest.ThumbnailView.as_view("thumbnail"))
app.add_url_rule("/metadata", view_func=rest.MetadataView.as_view("metadata"))
app.add_url_rule(
    "/bounds",
    view_func=rest.BoundsView.as_view("bounds"),
)
app.add_url_rule(
    "/tiles/<int:z>/<int:x>/<int:y>.png", view_func=rest.TilesView.as_view("tiles")
)
app.add_url_rule(
    "/tiles/debug/<int:z>/<int:x>/<int:y>.png",
    view_func=rest.TilesDebugView.as_view("tiles-debug"),
)
app.add_url_rule(
    "/region/world/<float:left>/<float:right>/<float:bottom>/<float:top>/region.tif",
    view_func=rest.RegionWorldView.as_view("region-world"),
)
app.add_url_rule(
    "/region/pixel/<int:left>/<int:right>/<int:bottom>/<int:top>/region.tif",
    view_func=rest.RegionPixelView.as_view("region-pixel"),
)
