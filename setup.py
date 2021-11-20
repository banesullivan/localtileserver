from io import open as io_open
import os
from setuptools import find_packages, setup

dirname = os.path.dirname(__file__)
readme_file = os.path.join(dirname, "README.md")
if os.path.exists(readme_file):
    with io_open(readme_file) as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ""

__version__ = None
version_file = os.path.join(dirname, "version.py")
with io_open(version_file, mode="r") as fd:
    exec(fd.read())

setup(
    name="flask-tileserver",
    version=__version__,
    description="Locally serve raster image tiles in the Slippy Map OGC standard.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Bane Sullivan",
    author_email="banesullivan@gmail.com",
    url="https://github.com/banesullivan/flask-tileserver",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python",
    ],
    python_requires=">=3.6",
    install_requires=[
        "flask",
        "Flask-Caching",
        "GDAL",
        "large_image",
        "large_image_source_gdal",
    ],
    extras_require={"leaflet": ["ipyleaflet"]},
)
