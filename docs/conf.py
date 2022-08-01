# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "PyTeal"
copyright = "2022, Algorand"
author = "Algorand"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
source_suffix = [".rst"]
master_doc = "index"

napoleon_include_init_with_doc = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


class NitpickIgnore:
    @staticmethod
    def optional() -> list[tuple[str, str]]:
        """
        Ignores parameter declarations that specify _optional_ usage.
        """
        return [
            ("py:class", "optional"),
        ]

    @staticmethod
    def standard_library() -> list[tuple[str, str]]:
        """
        Ignores Python standard library references that Sphinx does not track.
        """
        return [
            ("py:class", "abc.ABC"),
        ]


class NitpickIgnoreRegex:
    @staticmethod
    def type_vars() -> list[tuple[str, str]]:
        """
        Regex ignores generic TypeVar definitions that Sphinx does not track.
        """
        return [
            ("py.obj", r".*\.T$"),
            ("py.obj", r".*\.T[0-9]+$"),
            ("py.class", r".*\.T_co$"),
            ("py.obj", r".*\.T_co$"),
            ("py.class", r".*\.T$"),
            ("py.class", r"^T$"),
            ("py.obj", r".*\.N$"),
            ("py.class", r".*\.N$"),
            ("py.class", r"^N$"),
        ]

    @staticmethod
    def standard_library() -> list[tuple[str, str]]:
        """
        Regex ignores Python standard library references that Sphinx does not track.
        """
        return [
            ("py:class", r"contextlib\..*"),
            ("py:class", r"enum\..*"),
        ]

    @staticmethod
    def third_party() -> list[tuple[str, str]]:
        """
        Regex ignores 3rd party references that Sphinx does not track.
        """
        return [
            ("py:class", r"algosdk\.abi\..*"),
        ]


nitpick_ignore = NitpickIgnore.optional() + NitpickIgnore.standard_library()

nitpick_ignore_regex = (
    NitpickIgnoreRegex.standard_library()
    + NitpickIgnoreRegex.third_party()
    + NitpickIgnoreRegex.type_vars()
)


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]
