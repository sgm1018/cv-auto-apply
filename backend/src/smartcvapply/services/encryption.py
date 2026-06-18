"""Encryption utilities: Fernet for API keys, AES-256-GCM for CV files."""
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def encrypt_api_key(plaintext: str, *, fernet_key: str) -> str:
    return Fernet(fernet_key.encode()).encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str, *, fernet_key: str) -> str:
    try:
        return Fernet(fernet_key.encode()).decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Invalid Fernet token") from e


def derive_cv_key(*, master_key: str, user_id: str) -> bytes:
    master = master_key.encode()
    salt = user_id.encode()
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                info=b"smartcvapply-cv-key")
    return hkdf.derive(master)


def encrypt_cv_bytes(data: bytes, *, key: bytes) -> bytes:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, data, associated_data=None)
    return nonce + ct


def decrypt_cv_bytes(blob: bytes, *, key: bytes) -> bytes:
    nonce, ct = blob[:12], blob[12:]
    return AESGCM(key).decrypt(nonce, ct, associated_data=None)
