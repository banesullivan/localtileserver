# localtileserver examples

Jupyter notebooks demonstrating `localtileserver` with `ipyleaflet`.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/banesullivan/localtileserver/HEAD?labpath=examples/example.ipynb)

| Notebook                             | Shows                                                                                            |
| ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| [`example.ipynb`](example.ipynb)     | The basic pattern: `TileClient` + `get_leaflet_tile_layer` on a local and a remote (URL) raster. |
| [`hillshade.ipynb`](hillshade.ipynb) | Compute a hillshade from a DEM and compare the source against the hillshade in a split map.      |
| [`url_cog.ipynb`](url_cog.ipynb)     | Serve tiles from a COG hosted on S3 without downloading it.                                      |

Click the Binder badge above, or run any of the notebooks locally with `jupyter lab`.
