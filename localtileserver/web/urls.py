from localtileserver.web import rest, views
from localtileserver.web.blueprint import tileserver

# Views/pages
tileserver.add_url_rule("/", view_func=views.CesiumViewer.as_view("index"))
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
    "/tiles/<int:z>/<int:x>/<int:y>.<string:format>",
    endpoint="tiles",
)
rest.api.add_resource(
    rest.ListPalettes,
    "/palettes",
    endpoint="palettes",
)
rest.api.add_resource(
    rest.ValidateCOGView,
    "/validate",
    endpoint="validate",
)
