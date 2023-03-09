from configparser import ConfigParser
from contextlib import contextmanager
from unittest import mock

import pytest


@contextmanager
def mock_ConfigParser_context():
    patcher = mock.patch.object(
        ConfigParser, "getboolean", side_effect=Exception("1337")
    )
    patcher.start()
    yield
    patcher.stop()


@pytest.mark.serial
def test_sourcemap_fails_elegantly_when_no_ini():
    from examples.application.abi.algobank import router
    from pyteal import OptimizeOptions
    from pyteal.errors import SourceMapDisabledError

    with mock_ConfigParser_context():
        with pytest.raises(SourceMapDisabledError) as smde:
            router.compile(
                version=6,
                optimize=OptimizeOptions(scratch_slots=True),
                with_sourcemaps=True,
            )

    assert "pyteal.ini" in str(smde.value)
    assert "1337" not in str(smde.value)
