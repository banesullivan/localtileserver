from localtileserver.tileserver import rest, views
from localtileserver.tileserver.blueprint import tileserver

# Views/pages
tileserver.add_url_rule("/", view_func=views.CesiumViewer.as_view("index"))
tileserver.add_url_rule("/roi/", view_func=views.GeoJSViewer.as_view("roi"))

# REST endpoints
tileserver.add_url_rule("/thumbnail", view_func=rest.ThumbnailView.as_view("thumbnail"))
tileserver.add_url_rule("/metadata", view_func=rest.MetadataView.as_view("metadata"))
tileserver.add_url_rule(
    "/bounds",
    view_func=rest.BoundsView.as_view("bounds"),
)
tileserver.add_url_rule(
    "/tiles/<int:z>/<int:x>/<int:y>.png", view_func=rest.TileView.as_view("tiles")
)
tileserver.add_url_rule(
    "/tiles/debug/<int:z>/<int:x>/<int:y>.png",
    view_func=rest.TileDebugView.as_view("tiles-debug"),
)
tileserver.add_url_rule(
    "/world/region.tif",
    view_func=rest.RegionWorldView.as_view("region-world"),
)
tileserver.add_url_rule(
    "/pixel/region.tif",
    view_func=rest.RegionPixelView.as_view("region-pixel"),
)
