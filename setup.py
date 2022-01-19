#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import re
from setuptools import find_packages, setup


def get_version():
    fn = os.path.join("src", "kent", "__init__.py")
    vsre = r"""^__version__ = ['"]([^'"]*)['"]"""
    version_file = open(fn).read()
    return re.search(vsre, version_file, re.M).group(1)


def get_file(fn):
    with open(fn) as fp:
        return fp.read()


INSTALL_REQUIRES = ["flask<3"]
EXTRAS_REQUIRE = {
    "dev": [
        "black==21.12b0",
        "flake8==4.0.1",
        "pytest==6.2.5",
        "sentry-sdk==1.5.2",
        "tox==3.24.5",
        "tox-gh-actions==2.9.1",
        "twine==3.7.1",
    ]
}


setup(
    name="kent",
    version=get_version(),
    description="Fake Sentry service for debugging and integration tests",
    long_description=get_file("README.rst"),
    author="Will Kahn-Greene",
    author_email="willkg@mozilla.com",
    url="https://github.com/willkg/kent",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="MPLv2",
    zip_safe=False,
    keywords="sentry integration service",
    entry_points="""
        [console_scripts]
        kent-server=kent.cli_server:main
        kent-testpost=kent.cli_testpost:main
    """,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    project_urls={
        "Tracker": "https://github.com/willkg/kent/issues",
        "Source": "https://github.com/willkg/kent/",
    },
)
