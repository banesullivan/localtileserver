from localtileserver.tileserver import rest, views
from localtileserver.tileserver.blueprint import tileserver

# Views/pages
tileserver.add_url_rule("/", view_func=views.CesiumViewer.as_view("index"))
tileserver.add_url_rule("/roi/", view_func=views.GeoJSViewer.as_view("roi"))
tileserver.add_url_rule("/split/", view_func=views.CesiumSplitViewer.as_view("split"))
tileserver.add_url_rule("/split/form/", view_func=views.SplitViewForm.as_view("split-form"))

# REST endpoints
rest.api.add_resource(
    rest.ThumbnailView,
    "/thumbnail.<string:format>",
    endpoint="thumbnail",
)
rest.api.add_resource(
    rest.MetadataView,
    "/metadata",
    endpoint="metadata",
)
rest.api.add_resource(
    rest.BoundsView,
    "/bounds",
    endpoint="bounds",
)
rest.api.add_resource(
    rest.TileView,
    "/tiles/<int:z>/<int:x>/<int:y>.png",
    endpoint="tiles",
)
rest.api.add_resource(
    rest.TileDebugView,
    "/tiles/debug/<int:z>/<int:x>/<int:y>.png",
    endpoint="tiles-debug",
)
rest.api.add_resource(
    rest.RegionWorldView,
    "/world/region.tif",
    endpoint="region-world",
)
rest.api.add_resource(
    rest.RegionPixelView,
    "/pixel/region.tif",
    endpoint="region-pixel",
)
rest.api.add_resource(
    rest.ListPalettes,
    "/palettes",
    endpoint="palettes",
)
rest.api.add_resource(
    rest.PixelView,
    "/pixel",
    endpoint="pixel",
)
rest.api.add_resource(
    rest.HistogramView,
    "/histogram",
    endpoint="histogram",
)
rest.api.add_resource(
    rest.ListTileSources,
    "/sources",
    endpoint="sources",
)
rest.api.add_resource(
    rest.ValidateCOGView,
    "/validate",
    endpoint="validate",
)
