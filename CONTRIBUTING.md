# Contribution Guide

If you are interested in contributing to the project, we welcome and thank you. We want to make the best decentralized and effective blockchain platform available and we appreciate your willingness to help us.

## Filing Issues

Did you discover a bug? Do you have a feature request? Filing issues is an easy way anyone can contribute and helps us improve PyTeal. We use GitHub Issues to track all known bugs and feature requests.

Before logging an issue be sure to check current issues, check the [open GitHub issues][issues_url] to see if your issue is described there.

If you’d like to contribute to any of the repositories, please file a [GitHub issue][issues_url] using the issues menu item. Make sure to specify whether you are describing a bug or a new enhancement using the **Bug report** or **Feature request** button.

See the GitHub help guide for more information on [filing an issue](https://help.github.com/en/articles/creating-an-issue).

## Contribution Model

For each of our repositories we use the same model for contributing code. Developers wanting to  contribute must create pull requests. This process is described in the GitHub [Creating a pull request from a fork](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) documentation. Each pull request should be initiated against the master branch in the PyTeal repository.  After a pull request is submitted the core development team will review the submission and communicate with the developer using the comments sections of the PR. After the submission is reviewed and approved, it will be merged into the master branch of the source. These changes will be merged to our release branch on the next viable release date.

## Code Guidelines

We make a best-effort attempt to adhere to [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).  Keep the following context in mind:
* Our default stance is to run linter checks during the build process.
* Notable exception:  [naming conventions](https://peps.python.org/pep-0008/#naming-conventions).

### Naming Convention Guidelines
Since PyTeal aims for backwards compatibility, it's _not_ straightforward to change naming conventions in public APIs.  Consequently, the repo contains some deviations from PEP 8 naming conventions.

In order to retain a consistent style, we prefer to continue deviating from PEP 8 naming conventions in the following cases.  We try to balance minimizing exceptions against providing a consistent style for existing software.
* Enums - Define with lowercase camelcase.  Example:  https://github.com/algorand/pyteal/blob/7c953f600113abcb9a31df68165b61a2c897f591/pyteal/ast/txn.py#L37
* Factory methods - Define following [class name](https://peps.python.org/pep-0008/#class-names) conventions.  Example:  https://github.com/algorand/pyteal/blob/7c953f600113abcb9a31df68165b61a2c897f591/pyteal/ast/ternaryexpr.py#L63

Since it's challenging to enforce these exceptions with a linter, we rely on PR creators and reviewers to make a best-effort attempt to enforce agreed upon naming conventions.

### Module Guidelines

Every directory containing source code should be a Python module, meaning it should have an `__init__.py` file. This `__init__.py` file is responsible for exporting all public objects (i.e. classes, functions, and constants) for use outside of that module.

Modules may be created inside of other modules, in which case the deeper module is called a submodule or child module, and the module that contains it is called the parent module. For example, `pyteal` is the parent module to `pyteal.ast`.

A sibling module is defined as a different child module of the parent module. For example, `pyteal.ast` and `pyteal.ir` are sibling modules.

### Import Guidelines

#### In Runtime Code

When a runtime file in this codebase needs to import another module/file in this codebase, you should import the absolute path of the module/file, not the relative one, using the `from X import Y` method.

With regard to modules, there are two ways to import an object from this codebase:

* When importing an object from the same module or a parent module, you should import the full path of the source file that defines the object. For example:
    * (Import from same module): If `pyteal/ast/seq.py` needs to import `Expr` defined in `pyteal/ast/expr.py`, it should use `from pyteal.ast.expr import Expr`. **DO NOT** use `from pyteal.ast import Expr` or `from pyteal import Expr`, as this will cause an unnecessary circular dependency.
    * (Import from parent module): If `pyteal/ast/seq.py` needs to import `TealType` defined in `pyteal/types.py`, it should use `from pyteal.types import TealType`. **DO NOT** use `from pyteal import TealType`, as this will cause an unnecessary circular dependency.

* When importing an object from a child module or sibling module, you should import the entire module folder and access the desired object from there. Do not directly import the file that defines the object. For example:
    * (Import from child module): If `pyteal/compiler/compiler.py` needs to import `OptimizeOptions` from `pyteal/compiler/optimizer/optimizer.py`, it should use `from pyteal.compiler.optimizer import OptimizeOptions`. **DO NOT** use `from pyteal.compiler.optimizer.optimizer import OptimizeOptions`, as this will bypass the file `pyteal/compiler/optimizer/__init__.py`, which carefully defines the exports for the `pyteal.compiler.optimizer` module.
    * (Import from sibling module): If `pyteal/compiler/compiler.py` needs to import `Expr` defined in `pyteal/ast/expr.py`, it should use `from pyteal.ast import Expr`. **DO NOT** use `from pyteal import Expr`, as this will cause an unnecessary circular dependency, nor `from pyteal.ast.expr import Expr`, as this will bypass the file `pyteal/ast/__init__.py`, which carefully defines the
    exports for the `pyteal.ast` module.

When this approach is followed properly, circular dependencies can happen in two ways:
1. **Intra-module circular dependencies**, e.g. `m1/a.py` imports `m1/b.py` which imports `m1/a.py`. 
   When this happens, normally one of the files only needs to import the other to implement something,
   so the import statements can be moved from the top of the file to the body of the function that
   needs them. This breaks the import cycle.

2. **Inter-module circular dependencies**, e.g. `m1/a.py` imports module `m1/m2/__init__.py` which 
   imports `m1/m2/x.py` which imports `m1/a.py`. To avoid this, make sure that any objects/files in
   `m1` that need to be exposed to deeper modules do not rely on any objects from that deeper module.
   If that isn’t possible, then perhaps `m1/a.py` belongs in the `m1/m2/` module.

#### In Test Code

Test code is typically any file that ends with `_test.py` or is in the top-level `tests` folder. In
order to have a strong guarantee that we are testing in a similar environment to consumers of this
library, test code is encouraged to import _only_ the top-level PyTeal module, either with
`from pyteal import X, Y, Z` or `import pyteal as pt`.

This way we can be sure all objects that should be publicly exported are in fact accessible from the top-level module.

The only exception to this should be if the tests are for a non-exported object, in which case it is
necessary to import the object according to the runtime rules in the previous section.
