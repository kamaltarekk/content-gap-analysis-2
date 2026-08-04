import pytest

from app.services.collector import UnsafeUrlError, validate_public_url


def test_rejects_localhost() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_url("http://127.0.0.1/private")
