"""Tests for the core utility services."""
import pytest

from smartcvapply.services.encryption import (
    decrypt_api_key,
    decrypt_cv_bytes,
    derive_cv_key,
    encrypt_api_key,
    encrypt_cv_bytes,
)

VALID_FERNET = "jYbqgCuMy004d4KbFRAcSRtwg8ImpLefLABtUlF_AaU="


def test_api_key_roundtrip() -> None:
    ct = encrypt_api_key("sk-test-123", fernet_key=VALID_FERNET)
    assert ct != "sk-test-123"
    assert decrypt_api_key(ct, fernet_key=VALID_FERNET) == "sk-test-123"


def test_cv_roundtrip() -> None:
    master = "a" * 32
    key = derive_cv_key(master_key=master, user_id="u-1")
    data = b"PDF-binary-content"
    blob = encrypt_cv_bytes(data, key=key)
    assert blob != data
    assert decrypt_cv_bytes(blob, key=key) == data


def test_derive_cv_key_differs_per_user() -> None:
    master = "a" * 32
    k1 = derive_cv_key(master_key=master, user_id="u-1")
    k2 = derive_cv_key(master_key=master, user_id="u-2")
    assert k1 != k2
