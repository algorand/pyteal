from unittest import mock

import pytest

from pyteal.errors import AlgodClientError
from pyteal.util import algod_with_assertion


def test_algod_with_assertion_copacetic():
    """
    In C.I. integration tests we expect the happy path for the Algod client
    """
    client = algod_with_assertion()

    assert client

    reclient = algod_with_assertion(client)
    assert client is reclient


def test_algod_errors():
    from algosdk.v2client.algod import AlgodClient

    from pyteal import util

    with mock.patch.object(util, "_algod_client", side_effect=Exception("1337")):
        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion()
        assert "1337" in str(ace)

        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion(msg="okey dokey")
        assert "1337" in str(ace)
        assert "okey dokey" in str(ace)

    with mock.patch.object(AlgodClient, "status", side_effect=Exception("42")):
        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion()
        assert "42" in str(ace)

        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion(msg="yoyo ma")
        assert "42" in str(ace)
        assert "yoyo ma" in str(ace)

    with mock.patch.object(AlgodClient, "status", lambda _: None):
        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion()
        assert "did not produce any results" in str(ace)

        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion(msg="mellow yellow")
        assert "did not produce any results" in str(ace)
        assert "mellow yellow" in str(ace)

    with pytest.raises(AlgodClientError) as ace:
        algod_with_assertion("foo")  # type: ignore
    assert "has no attribute 'status'" in str(ace)

    with pytest.raises(AlgodClientError) as ace:
        algod_with_assertion("foo", msg="blarney")  # type: ignore
    assert "has no attribute 'status'" in str(ace)
    assert "blarney" in str(ace)

    client = algod_with_assertion()
    assert client

    with mock.patch.object(client, "status", side_effect=Exception("42")):
        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion(client)
        assert "42" in str(ace)

        with pytest.raises(AlgodClientError) as ace:
            algod_with_assertion(client, msg="hokus pokus")
        assert "42" in str(ace)
        assert "hokus pokus" in str(ace)
