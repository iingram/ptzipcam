import setuptools


setuptools.setup(
    name="ptzipcam",
    author="Ian Ingram",
    version="0.0.1",
    author_email="ianishidden@gmail.com",
    description="For controlling PTZ IP cameras that support ONVIF.",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
