"""Authenticated file encryption; envelope keys remain on the backend."""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def master_key():
    try:
        key = base64.b64decode(os.environ.get("CONTENT_MASTER_KEY", ""), validate=True)
    except ValueError:
        raise ValueError("Protected storage is not configured") from None
    if len(key) != 32:
        raise ValueError("Protected storage is not configured")
    return key


def seal(data: bytes, content_hash: str):
    master = master_key()
    key = AESGCM.generate_key(bit_length=256)
    nonce, wrap_nonce = os.urandom(12), os.urandom(12)
    aad = content_hash.encode("ascii")
    ciphertext = nonce + AESGCM(key).encrypt(nonce, data, aad)
    wrapped = wrap_nonce + AESGCM(master).encrypt(wrap_nonce, key, aad)
    return ciphertext, base64.b64encode(wrapped).decode("ascii")


def unseal(ciphertext: bytes, wrapped: str, content_hash: str):
    envelope = base64.b64decode(wrapped, validate=True)
    aad = content_hash.encode("ascii")
    key = AESGCM(master_key()).decrypt(envelope[:12], envelope[12:], aad)
    return AESGCM(key).decrypt(ciphertext[:12], ciphertext[12:], aad)
