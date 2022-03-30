#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

test_requirements = [
    "black==22.3.0",
    "graviton@git+https://github.com/algorand/graviton@🦙",
    "mypy==0.931",
    "py-algorand-sdk",
    "pytest",
    "pytest-cov",
    "pytest-timeout",
    "tabulate==0.8.9",
]

setuptools.setup(
    name="pyteal",
    version="0.10.1",
    author="Algorand",
    author_email="pypiservice@algorand.com",
    description="Algorand Smart Contracts in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/pyteal",
    packages=setuptools.find_packages(),
    install_requires=["py-algorand-sdk"],
    extras_require={"test": test_requirements},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={"pyteal": ["*.pyi"]},
    python_requires=">=3.6",
)
