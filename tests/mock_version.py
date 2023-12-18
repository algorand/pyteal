import pytest
from importlib import metadata


@pytest.fixture
def mock_version(version: str, monkeypatch: pytest.MonkeyPatch):
    def mocked_version(name: str):
        if (
            name == "pyteal"
            and version is not None  # don't mock if no version is specified
        ):
            return version
        else:
            return metadata.version(name)

    monkeypatch.setattr(metadata, "version", mocked_version)
