#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyteal",
    version="0.11.1",
    author="Algorand",
    author_email="pypiservice@algorand.com",
    description="Algorand Smart Contracts in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/pyteal",
    packages=setuptools.find_packages(),
    install_requires=["py-algorand-sdk"],
    extras_require={
        "development": [
            "black==22.3.0",
            "flake8==4.0.1",
            "flake8-tidy-imports==4.6.0",
            "mypy==0.942",
            "pytest==7.1.1",
            "pytest-cov==3.0.0",
            "pytest-timeout==2.1.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={"pyteal": ["*.pyi"]},
    python_requires=">=3.10",
)
