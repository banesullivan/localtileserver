# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


import datetime

import localtileserver

# -- Project information -----------------------------------------------------


project = "🌐 localtileserver"
year = datetime.date.today().year
copyright = f"2021-{year}, Bane Sullivan"
author = "Bane Sullivan"

# The full version, including alpha/beta/rc tags
release = localtileserver.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "notfound.extension",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "jupyter_sphinx",
    "sphinx_copybutton",
    # "sphinx_panels",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "friendly"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

html_title = project
html_short_title = ""
# html_favicon = "_static/favicon.png"
html_extra_path = []  # TODO: "CNAME",
html_use_smartypants = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
html_context = {
    "github_user": "banesullivan",
    "github_repo": "localtileserver",
    "github_version": "main",
    "doc_path": "doc",
}

html_theme_options = {
    "default_mode": "light",
    "google_analytics_id": "G-14GFZDPSQG",
    "show_prev_next": False,
    "github_url": "https://github.com/banesullivan/localtileserver",
    "icon_links": [
        {
            "name": "Support",
            "url": "https://github.com/banesullivan/localtileserver/discussions",
            "icon": "fa fa-comment fa-fw",
        },
        {
            "name": "Demo",
            "url": "https://tileserver.banesullivan.com/",
            "icon": "fa fa-desktop fa-fw",
        },
        {
            "name": "Author",
            "url": "https://banesullivan.com/",
            "icon": "fa fa-user fa-fw",
        },
    ],
    "navbar_end": ["navbar-icon-links"],
    "logo": {
        "image_light": "logo-light.png",
        "image_dark": "logo-dark.png",
    },
}

html_sidebars = {
    "index": [],
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


notfound_context = {
    "body": """
<h1>Page not found.</h1>\n\nPerhaps try the <a href="/">home page.</a>.
<br>
<p>In the meantime, here's a bonus tile layer</p>
<br>
<div id="map" style="width: 100%; height: 400px;"></div>
<script>
var map = L.map('map').setView([39.49, -108.507], 9);

L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}.png', {
    attribution: 'Map tiles by <a href="https://carto.com">Carto</a>, under CC BY 3.0. Data by <a href="https://www.openstreetmap.org/">OpenStreetMap</a>, under ODbL.'
}).addTo(map);

L.tileLayer('https://tileserver.banesullivan.com/api/tiles/{z}/{x}/{y}.png?projection=EPSG:3857&filename=https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif', {
    attribution: 'Raster file served by <a href="https://github.com/banesullivan/localtileserver" target="_blank">localtileserver</a>.',
    subdomains: '',
    crossOrigin: false,
}).addTo(map);


</script>

<br>
""",
}
notfound_no_urls_prefix = True

# Copy button customization
# exclude traditional Python prompts from the copied code
copybutton_prompt_text = r">>> ?|\.\.\. "
copybutton_prompt_is_regexp = True


def setup(app):
    app.add_css_file("copybutton.css")
    app.add_css_file("no_search_highlight.css")
    app.add_css_file("fontawesome/css/all.css")
