from configparser import ConfigParser
from unittest import mock

import pytest


@pytest.fixture
def mock_ConfigParser():
    patcher = mock.patch.object(
        ConfigParser, "getboolean", side_effect=Exception("1337")
    )
    patcher.start()
    yield
    patcher.stop()


@pytest.mark.serial
def test_sourcemap_fails_elegantly_when_no_ini(mock_ConfigParser):
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.errors import SourceMapDisabledError

    with pytest.raises(SourceMapDisabledError) as smde:
        router.compile(
            version=6,
            optimize=OptimizeOptions(scratch_slots=True),
            with_sourcemaps=True,
        )

    assert "pyteal.ini" in str(smde.value)
    assert "1337" not in str(smde.value)
