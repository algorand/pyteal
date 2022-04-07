# Contribution Guide

If you are interested in contributing to the project, we welcome and thank you. We want to make the best decentralized and effective blockchain platform available and we appreciate your willingness to help us.



# Filing Issues

Did you discover a bug? Do you have a feature request? Filing issues is an easy way anyone can contribute and helps us improve PyTeal. We use GitHub Issues to track all known bugs and feature requests.

Before logging an issue be sure to check current issues, check the [Developer Frequently Asked Questions](https://developer.algorand.org/docs/developer-faq) and [GitHub issues][issues_url] to see if your issue is described there.

If you’d like to contribute to any of the repositories, please file a [GitHub issue][issues_url] using the issues menu item. Make sure to specify whether you are describing a bug or a new enhancement using the **Bug report** or **Feature request** button.

See the GitHub help guide for more information on [filing an issue](https://help.github.com/en/articles/creating-an-issue).

# Contribution Model

For each of our repositories we use the same model for contributing code. Developers wanting to contribute must create pull requests. This process is described in the GitHub [Creating a pull request from a fork](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) documentation. Each pull request should be initiated against the master branch in the Algorand repository.  After a pull request is submitted the core development team will review the submission and communicate with the developer using the comments sections of the PR. After the submission is reviewed and approved, it will be merged into the master branch of the source. These changes will be merged to our release branch on the next viable release date.

# Code Guidelines

We make a best-effort attempt to adhere to [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).  Keep the following context in mind:
* Our default stance is to run linter checks during the build process.
* Notable exception:  [naming conventions](https://peps.python.org/pep-0008/#naming-conventions).

## Naming Convention Guidelines
Since PyTeal aims for backwards compatibility, it's _not_ straightforward to change naming conventions in public APIs.  Consequently, the repo contains some deviations from PEP 8 naming conventions.

In order to retain a consistent style, we prefer to continue deviating from PEP 8 naming conventions in the following cases.  We try to balance minimizing exceptions against providing a consistent style for existing software.
* Enums - Define with lowercase camelcase.  Example:  https://github.com/algorand/pyteal/blob/7c953f600113abcb9a31df68165b61a2c897f591/pyteal/ast/txn.py#L37
* Factory methods - Define following [class name](https://peps.python.org/pep-0008/#class-names) conventions.  Example:  https://github.com/algorand/pyteal/blob/7c953f600113abcb9a31df68165b61a2c897f591/pyteal/ast/ternaryexpr.py#L63

Since it's challenging to enforce these exceptions with a linter, we rely on PR creators and reviewers to make a best-effort attempt to enforce agreed upon naming conventions.
