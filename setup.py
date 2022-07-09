import os
import re

import setuptools


def read(filename):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    with open(path, 'r') as f:
        return f.read()


def find_version(text):
    match = re.search(r"^__version__\s*=\s*['\"](.*)['\"]\s*$", text,
                      re.MULTILINE)
    return match.group(1)


DESC = "Package for controlling PTZ IP cameras that support ONVIF"

setuptools.setup(
    name="ptzipcam",
    description=DESC,
    license="MIT",
    author="Ian Ingram",
    version=find_version(read('ptzipcam/__init__.py')),
    packages=['ptzipcam'],
    install_requires=[
        'pyyaml',
        'opencv-python',
        'onvif-zeep',
        'screeninfo',
        'imutils',
        'camml',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Development Status :: 2 - Pre-Alpha',
        "Operating System :: OS Independent",
    ],
)
