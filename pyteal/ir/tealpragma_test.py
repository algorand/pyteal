import pytest
import pyteal as pt


def test_version():
    for i in range(10):
        version_pragma = pt.TealPragma(version=i)
        assert version_pragma._name == "version"
        assert version_pragma._value == i
        assert version_pragma.assemble() == f"#pragma version {i}"
        assert repr(version_pragma) == f"TealPragma(version={i})"


def test_type_track():
    for value in (True, False):
        type_track_pragma = pt.TealPragma(type_track=value)
        assert type_track_pragma._name == "typetrack"
        assert type_track_pragma._value == str(value).lower()
        assert type_track_pragma.assemble() == f"#pragma typetrack {str(value).lower()}"
        assert repr(type_track_pragma) == f"TealPragma(type_track={value})"


def test_empty():
    with pytest.raises(ValueError):
        pt.TealPragma()


def test_both():
    with pytest.raises(ValueError):
        pt.TealPragma(version=1, type_track=True)
