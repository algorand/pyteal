#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyteal", # Replace with your own username
    version="0.6.1",
    author="Shumo Chu",
    author_email="shumo.chu@gmail.com",
    description="Algorand Smart Contracts in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/pyteal",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
