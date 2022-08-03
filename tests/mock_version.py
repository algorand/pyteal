import pytest
import pkg_resources


@pytest.fixture
def mock_version(version: str, monkeypatch: pytest.MonkeyPatch):
    def mocked_require(name: str):
        if (
            name == "pyteal"
            and version is not None  # don't mock if no version is specified
        ):
            return [
                pkg_resources.Distribution(
                    version=version,
                )
            ]
        else:
            return pkg_resources.require(name)[0]

    monkeypatch.setattr(pkg_resources, "require", mocked_require)
