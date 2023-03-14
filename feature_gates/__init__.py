from dataclasses import dataclass
from typing import Final


@dataclass
class _FeatureGatesConfig:
    """
    Configuration for feature gates.

    We follow the following convention:

    feature_property: True/False
    """

    sourcemap_enabled: bool
    sourcemap_debug: bool


class FeatureGates:
    # default values for feature gates:
    _gates: Final[_FeatureGatesConfig] = _FeatureGatesConfig(
        sourcemap_enabled=False,
        sourcemap_debug=False,
    )
    _features: Final[set[str]] = set(vars(_gates).keys())
    verbose: bool = False

    @classmethod
    def _make_feature(cls, feature: str):
        setattr(cls, feature, classmethod(lambda cls: cls.get(feature)))
        setattr(
            cls, f"set_{feature}", classmethod(lambda cls, gate: cls.set(feature, gate))
        )

    @classmethod
    def get(cls, feature: str) -> bool | None:
        if feature not in cls._features:
            raise ValueError(
                f"Unknown {feature=} (available features: {cls._features}))"
            )

        return getattr(cls._gates, feature)

    @classmethod
    def set(cls, feature: str, gate: bool) -> None:
        if feature not in cls._features:
            raise ValueError(
                f"Cannot set unknown {feature=} (available features: {cls._features}))"
            )
        setattr(cls._gates, feature, gate)


for feature in FeatureGates._features:
    FeatureGates._make_feature(feature)
