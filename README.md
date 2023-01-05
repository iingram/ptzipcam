# Overview

Package of tools for interfacing with PTZ network surveillance cameras
and controlling them in responsive and programmatic ways.

# Hardware

- a Pan-Tilt-Zoom networked surveillance camera that has good
  compliance with the ONVIF protocol.  ptzipcam has been the most
  tested with Hikvision cameras.

- a computer to run the software (tested on a few x86_64 systems and
  on Raspberry Pi 4 Model B devices)

- ethernet cable to connect the camera to the computer

- power source for the camera 

# Operating System

Currently, ptzipcam has been tested on Ubuntu 18.04 and 20.04 on
x86_64 machines and Raspian Buster on Pis (ARM CPU)

# Installation instructions

## From PyPI

    pip install ptzipcam

Note you probably still will need to install the WSDL files as
outlined below.  However, the instructions below do assume you have
installed ptzipcam in a virtual environment and that you have some
WSDL files to work with (some are included in the package code repo
itself)

## From GitHub repo

### Clone the ptzipcam repository

    git clone git@github.com:iingram/ptzipcam.git

### Set up a virtual environment

It is recommended to create a virtual environment to work within.

Install the virtualenv packages we need:

    sudo pip3 install virtualenv virtualenvwrapper

Setup virtual environment tools:

```sh
echo -e "\n# Virtual environment setup" >> ~/.bashrc
echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
source ~/.bashrc
```

Create a virtual environment for the ptzipcam project:

    mkvirtualenv ptzipcam_env

Note that ptzipcam requires Python 3 so if the default on your system is
Python 2, make sure the virtual environment will use Python 3:

    mkvirtualenv ptzipcam_env -p python3

Activate virtual environment (not necessary if you just made it)

    workon ptzipcam_env

### Run install script

   ./install.sh

### Testing

To verify everything is configured properly you can try one of the
example applications.  Some of these require more hardware and
packages so a good one to test with is this one:

    ./look_around_randomly.py cfgs/CONFIG_FILE.yaml

You'll notice the example takes a YAML configuration file as its only
CLI argument. An example configuration file is provided in ```cfgs/```
Some elements have to be configured for your particular setup
(e.g. the IP of the camera and user credentials for an account on the
camera (the account must have ONVIF privileges)).  For now it is
assumed that these are well-enough self-documented in the example
config file but when that turns out not to be the case, we'll provide
better documentation here, plus some documentation of the other
configuration parameters that should work with most cameras without
adjustment but that you might want to tune for your application.

## Installing WSDL files

For the ONVIF connection to the camera to work, WSDL files must be
placed in the appropriate place in the virtual environment files.

If you are installing from the repository, for convenience a set of
WSDL files are currently included in the repo so the following steps
should put them in the correct location (assuming you are still inside
of the local ptzipcam repo directory):

     cp wsdl/wsdl.tar.gz ~/.virtualenvs/ptzipcam_env/lib/python3.7/site-packages/
     cd ~/.virtualenvs/ptzipcam_env/lib/python3.7/site-packages/
     tar xzf wsdl.tar.gz
     rm wsdl.tar.gz
     cd -

