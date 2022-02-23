# Docs

`docs/` contains end user documentation geared towards writing smart contracts with PyTeal.  The README explains how to edit docs.

## Local testing

Pyteal uses [Sphinx](https://github.com/sphinx-doc/sphinx) to generate HTML from RST files.  Test changes by generating HTML and viewing with a web browser.

Here's the process:
* Perform one-time environment setup:
  * Create a virtual environment isolated to `docs/`.  Do _not_ mix with a top-level virtual environment.
  * Install dependencies via `pip`.
* Generate HTML docs:  `make html`.
* If successful, generated HTML is available in `docs/_build/html`.

Additionally, each PR commit generates HTML docs via [Github Actions](../.github/workflows/build.yml).

## Releasing

Production docs live at https://pyteal.readthedocs.io/en/stable/.  [Github Actions](../.github/workflows/build.yml) automate the releasing process.
