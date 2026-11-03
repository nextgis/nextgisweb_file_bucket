from setuptools import find_packages, setup

with open("VERSION") as fd:
    VERSION = fd.read().rstrip()

requires = [
    "nextgisweb>=5.7.0.dev1",
    "zipstream-new==1.1.*",
]

entry_points = {
    "nextgisweb.packages": [
        "nextgisweb_file_bucket = nextgisweb:single_component",
    ],
}

setup(
    name="nextgisweb_file_bucket",
    version=VERSION,
    description="File bucket extension for NextGIS Web",
    author="NextGIS",
    author_email="info@nextgis.com",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.14",
    install_requires=requires,
    entry_points=entry_points,
)
