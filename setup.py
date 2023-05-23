from io import open as io_open
import os

from setuptools import find_packages, setup

dirname = os.path.dirname(__file__)
readme_file = os.path.join(dirname, "README.md")
if os.path.exists(readme_file):
    with io_open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ""

# major, minor, patch
version_info = 0, 6, 4
# Nice string for the version
__version__ = ".".join(map(str, version_info))

setup(
    name="localtileserver",
    version=__version__,
    description="Locally serve geospatial raster tiles in the Slippy Map standard.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bane Sullivan",
    author_email="hello@banesullivan.com",
    url="https://github.com/banesullivan/localtileserver",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click",
        "flask>=2.0.0",
        "Flask-Caching",
        "flask-cors",
        "flask-restx>=0.5.0",
        "GDAL",
        "large-image[gdal]>=1.14.1",
        "requests",
        "server-thread",
        "scooby",
        "werkzeug",
    ],
    extras_require={
        "colormaps": ["matplotlib", "colorcet", "cmocean"],
        "sources": ["large-image[gdal,pil,tiff]>=1.14.1"],
        "jupyter": ["jupyter-server-proxy", "ipyleaflet", "folium"],
        "helpers": ["shapely", "rasterio"],
    },
    entry_points={
        "console_scripts": [
            "localtileserver = localtileserver.__main__:run_app",
        ],
    },
)
