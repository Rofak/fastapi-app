from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import base64

SECRET_KEY = b'12345678901234567890123456789012'  # 32 bytes = AES-256


def encrypt(data: str) -> str:
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()

    cipher = Cipher(
        algorithms.AES(SECRET_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(iv + encrypted).decode()


def decrypt(token: str) -> str:
    raw = base64.b64decode(token)

    iv = raw[:16]
    encrypted = raw[16:]

    cipher = Cipher(
        algorithms.AES(SECRET_KEY),
        modes.CBC(iv),
        backend=default_backend()
    )

    decryptor = cipher.decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()

    return data.decode()