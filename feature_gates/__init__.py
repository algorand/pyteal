from dataclasses import dataclass
from configparser import ConfigParser, NoOptionError, NoSectionError
from typing import Final
from pathlib import Path


@dataclass
class _FeatureGatesConfig:
    """
    Configuration for feature gates.

    We follow the following convention:

    feature_property: bool | None

    If the value is None, the feature is not set.

    To configure via `pyteal.ini`, the section should be `pyteal-feature`
    with values such as
    property = True

    For example, the fields:

    sourcemap_enabled: bool | None = None
    sourcemap_debug: bool | None = None

    imply a pyteal.ini file that looks something like:

    [pyteal-sourcemap]
    enabled = True
    debug = False
    """

    sourcemap_enabled: bool | None = None
    sourcemap_debug: bool | None = None


class FeatureGates:
    INI_FILENAME = "pyteal.ini"
    INI_SECTION_PREFIX = "pyteal-"
    DEFAULTS: Final[_FeatureGatesConfig] = _FeatureGatesConfig(
        sourcemap_enabled=False,
        sourcemap_debug=False,
    )
    _gates: Final[_FeatureGatesConfig] = _FeatureGatesConfig()
    _features: Final[set[str]] = set(vars(_gates).keys())
    verbose: bool = False

    @classmethod
    def _make_feature(cls, feature: str):
        setattr(cls, feature, classmethod(lambda cls: cls.get(feature)))
        setattr(
            cls, f"set_{feature}", classmethod(lambda cls, gate: cls.set(feature, gate))
        )

    @classmethod
    def _get(cls, feature: str) -> bool | None:
        """Return the value of the given feature."""
        if feature not in cls._features:
            raise ValueError(
                f"Unknown {feature=} (available features: {cls._features}))"
            )

        return getattr(cls._gates, feature)

    @classmethod
    def get(cls, feature: str) -> bool:
        if (gate := cls._get(feature)) is None:
            raise ValueError(f"Feature {feature} is not set")

        return gate

    @classmethod
    def _set(cls, feature: str, gate: bool, overwrite: bool) -> None:
        """Set the feature gate if it is unset, or overwrite == True."""
        current = cls._get(feature)
        if current is None or overwrite:
            setattr(cls._gates, feature, gate)

    @classmethod
    def set(cls, feature: str, gate: bool) -> None:
        """Set the feature gate for the given feature to the given value."""
        cls._set(feature, gate, overwrite=True)

    @classmethod
    def load(cls, *, overwrite: bool = False, config_path: str = ""):
        """
        Load the feature gates from pyteal.ini. If pyteal.ini does not exist,
        or if a feature is not set in pyteal.ini, then the feature gate will
        default to DEFAULTS.

        If `overwrite` is True, then the feature gates will be overwritten
        regardless of whether they are already set.

        If `config_path` is not empty, then the feature gates will be loaded
        from the current working directory's "pyteal.ini" file, unless an
        absolute path is provided.
        """
        if config_path:
            path = Path(config_path)
            if not path.is_absolute():
                path = Path.cwd() / config_path
        else:
            path = Path.cwd() / cls.INI_FILENAME

        if cls.verbose:
            print(f"Attempting to source feature gates from {path}.")

        config = ConfigParser()
        try:
            config.read(path)
        except Exception as e:
            if cls.verbose:
                print(f"Failed to load {path}: {e}. Proceed by using DEFAULTS.")
            return

        for feature_prop in cls._features:
            feature, prop = feature_prop.split("_")
            if cls._get(feature_prop) is None or overwrite:
                try:
                    gate = config.getboolean(f"{cls.INI_SECTION_PREFIX}{feature}", prop)
                except (NoSectionError, NoOptionError):
                    gate = getattr(cls.DEFAULTS, feature_prop)
                    if cls.verbose:
                        print(
                            f"Failed to load {feature_prop} from expected {path}. Defaulting to {gate=}."
                        )
                cls._set(feature_prop, gate, overwrite)

        for feature_prop in cls._features:
            # for validation purposes only:
            cls.get(feature_prop)


for feature in FeatureGates._features:
    FeatureGates._make_feature(feature)
