"""Setup.py for this project

"""

import os
import re

import setuptools


def read(filename):
    """Read file using path of this file to find it

    """
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    with open(path, 'r', encoding='utf-8') as readfile:
        return readfile.read()


def find_version(text):
    """Extract the version from a file

    Using regular expressions to find the string that looks like the
    version number

    """
    match = re.search(r"^__version__\s*=\s*['\"](.*)['\"]\s*$", text,
                      re.MULTILINE)
    return match.group(1)


AUTHOR = "Ian Ingram"
DESC = "Package for controlling PTZ IP cameras that support ONVIF"

setuptools.setup(
    name="ptzipcam",
    description=DESC,
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    license="MIT",
    version=find_version(read('ptzipcam/__init__.py')),
    author=AUTHOR,
    packages=['ptzipcam'],
    include_package_data=True,
    install_requires=[
        'numpy',
        'opencv-python',
        'onvif-zeep',
        'camml',
    ],
    extra_require={
        'examples': [
            'pyyaml',
            'imutils',
            'screeninfo',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: POSIX :: Linux',
    ],
)
