#!/usr/bin/env python3

from setuptools import setup


setup(
    name="finnixmirrors",
    description="mirrors.finnix.org",
    author="Ryan Finnie",
    packages=[
        "finnixmirrors",
        "finnixmirrors.migrations",
        "finnixmirrors.management.commands",
    ],
    include_package_data=True,
    install_requires=["Django", "django-xff", "requests", "python-dateutil"],
)
