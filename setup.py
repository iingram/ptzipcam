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
        'numpy==1.18.3',
        'pyyaml',
        'opencv-python==3.4.2.16',
        'onvif-zeep',
        'screeninfo',
        'imutils',
        'camml',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: POSIX :: Linux',
    ],
    # would like to add this as a CLI tool but currently needs config file...
    # entry_points = {
    #     'console_scripts': ['aim_ptz_w_keyboard=ptzipcam.utils.aim_ptz_w_keyboard:main']
    #},
)
