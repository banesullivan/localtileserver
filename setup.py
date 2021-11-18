from setuptools import find_packages, setup

setup(
    name="flask-tile-server",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "flask",
        "Flask-Caching",
        "GDAL",
        "large_image",
        "large_image_source_gdal",
    ],
)
