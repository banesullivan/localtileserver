from flask import render_template
from flask.views import View

from tileserver import utilities
from tileserver.application import app
from tileserver.application.paths import get_path


class Viewer(View):
    def dispatch_request(self):
        return render_template("tileviewer.html")


@app.context_processor
def inject_context():
    path = get_path()
    tile_source = utilities.get_tile_source(path)
    context = utilities.get_meta_data(tile_source)
    context["bounds"] = utilities.get_tile_bounds(tile_source, projection="EPSG:4326")
    context["path"] = path
    return context
