import re
from importlib import metadata
from typing import Any
from semantic_version import Version, NpmSpec

from pyteal.errors import TealPragmaError


def __convert_pep440_compiler_version(compiler_version: str):
    """Convert PEP 440 version identifiers to valid NPM versions.

    For example:
        "1.0.0" -> "1.0.0"
        "1.0.0a1" -> "1.0.0-a1"
        "<0.5.0+local || >=1.0.0a9.post1.dev2" -> "<0.5.0 || >=1.0.0-alpha9.1.2"
    """
    NUMBER = r"(?:x|X|\*|0|[1-9][0-9]*)"
    LOCAL = r"[a-zA-Z0-9.]*"
    TRIM_PREFIX_RE = re.compile(
        r"""
            (?:v)?                                          # Strip optional initial v
            (?P<op><|<=|>=|>|=|\^|~|)                       # Operator, can be empty
            (?P<major>{nb})(?:\.(?P<minor>{nb})(?:\.(?P<patch>{nb}))?)?
            (?:(?P<prerel_type>a|b|rc)(?P<prerel>{nb}))?    # Optional pre-release
            (?:\.post(?P<postrel>{nb}))?                    # Optional post-release
            (?:\.dev(?P<dev>{nb}))?                         # Optional dev release
            (?:\+(?P<local>{lcl}))?                         # Optional local version
        """.format(
            nb=NUMBER,
            lcl=LOCAL,
        ),
        re.VERBOSE,
    )

    def match_replacer(match: re.Match):
        (
            op,
            major,
            minor,
            patch,
            prerel_type,
            prerel,
            postrel,
            dev,
            local,
        ) = match.groups()

        # Base version (major/minor/patch)
        base_version = "{}.{}.{}".format(major or "0", minor or "0", patch or "0")

        # Combine prerel, postrel, and dev
        combined_additions = []
        short_prerel_type_to_long = {
            "a": "alpha",
            "b": "beta",
            "rc": "rc",
        }
        if prerel_type is not None:
            combined_additions.append(short_prerel_type_to_long[prerel_type] + prerel)
        if len(combined_additions) > 0 or postrel is not None or dev is not None:
            combined_additions.append(postrel or "0")
        if len(combined_additions) > 0 or dev is not None:
            combined_additions.append(dev or "0")
        combined_additions_str = ".".join(combined_additions)

        # Build full_version
        full_version = base_version
        if len(combined_additions) > 0:
            full_version += "-" + combined_additions_str
        if local is not None:
            full_version += "+" + local.lower()

        if op is not None:
            return op + full_version
        return full_version

    return re.sub(TRIM_PREFIX_RE, match_replacer, compiler_version)


def is_valid_compiler_version(compiler_version: str):
    """Check if the compiler version is valid.

    Args:
        compiler_version: The compiler version to check.

    Returns:
        True if the compiler version is a valid NPM specification range
        using either the PEP 440 or semantic version format, otherwise False.
    """
    try:
        pep440_converted = __convert_pep440_compiler_version(compiler_version)
        NpmSpec(pep440_converted)
        return True
    except ValueError:
        return False


def pragma(
    *,
    compiler_version: str,
    **kwargs: Any,
) -> None:
    """
    Specify pragmas for the compiler.

    Args:
        compiler_version: Acceptable versions of the compiler. Will fail if the current PyTeal version
            is not contained in the range. Follows the npm `semver range scheme <https://github.com/npm/node-semver#ranges>`_
            for specifying compatible versions.

    For example:

        .. code-block:: python

            # this will immediately fail if the current PyTeal version does not satisfy the
            # version constraint
            pragma(compiler_version="^0.14.0")
    """
    pkg_version = metadata.version("pyteal")
    pyteal_version = Version(__convert_pep440_compiler_version(pkg_version))
    if pyteal_version not in NpmSpec(
        __convert_pep440_compiler_version(compiler_version)
    ):
        raise TealPragmaError(
            "PyTeal version {} is not compatible with compiler version {}".format(
                pkg_version, compiler_version
            )
        )
