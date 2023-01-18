# PyTeal Release Process

This document contains information about how to issue a new PyTeal release.

## Release Steps

### 1. Prep files in repo 

In addition to the code changes that make up the release, a few files must be updated for each release we make.

Usually, both of these changes will happen in a "release PR." For example: https://github.com/algorand/pyteal/pull/637

#### a. Update `CHANGELOG.md`

The first section in `CHANGELOG.md` should be `Unreleased`. Ideally this section would be populated with all the changes since the last release and would have been updated with every PR. However, it's possible that some PRs may have forgotten to update the changelog. You should look at all the commits since the last release to see if anything that should be mentioned in the changelog is missing. If so, add it now.

Not _every_ PR needs to be reflected in the changelog. As a general rule, if and only if the PR makes a change that's visible to consumers of the PyTeal library (including documentation), then it should be included in the changelog. Changes to tests or development tools that do not affect library consumers should generally not be reported.

Once the `Unreleased` section is complete, change it to the version you are about to release, e.g. `v0.21.0`. If any subsections are empty, remove them.

At this point, add a new placeholder to the top of the file for future changelog additions, like so:

```
# Unreleased

## Added

## Changed

## Fixed
```

#### b. Bump version in `setup.py`

Update the `setup.py` file to contain the version you wish to release. For example:

```diff
--- a/setup.py
+++ b/setup.py
@@ -7,7 +7,7 @@
 
 setuptools.setup(
     name="pyteal",
-    version="0.20.1",
+    version="0.21.0",
     author="Algorand",
     author_email="pypiservice@algorand.com",
     description="Algorand Smart Contracts in Python",
```

### 2. Create a GitHub release & tag

Once the changes from step 1 have been committed to the repo, it's time to issue the release.

Navigate to GitHub's "Draft a new release" page: https://github.com/algorand/pyteal/releases/new. Fill out the fields like so:
* Tag: create a new tag with the version you're about to release, e.g. `v0.21.0`
* Title: the version you're about to release. This should be the same as the tag.
* Description: copy and paste the release notes from `CHANGELOG.md`. Do not include the section header with the release version, since it's redundant.

Press "Publish release" to submit. This was create a new git tag, which triggers a GitHub Actions job of ours to build and upload a release to PyPI.

### 3. Check outputs to ensure success

After you've kicked off a release as described in the previous section, you should monitor the process to ensure everything succeeds. Unfortunately we don't have any notifications if the release process fails, so it's important to perform these manual checks.

#### a. Ensure GitHub Actions job succeeds

Visit https://github.com/algorand/pyteal/actions to find the GitHub Actions job that's running the release. Open it and ensure it succeeds.

#### b. Check that PyPI receives the release

Visit https://pypi.org/project/pyteal/ to check that the latest release is listed in PyPI.

#### c. Ensure docs are updated

Issuing a git tag also triggers ReadTheDocs to generate new documentation.

Visit https://readthedocs.org/projects/pyteal/builds/ to ensure that the docs build for the release succeeds.

Then, visit https://pyteal.readthedocs.io/ to ensure that the latest release is present on our docs site. In the bottom left corner, there's a button that will display the current version of the docs, e.g. `v: stable`. Click this to see all versions that are available. Ensure that the just released version is there, and click it to bring up that specific version's docs. Manually inspect the site to ensure documentation was generated successfully.

