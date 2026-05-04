from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY  # must match frontend
IV_KEY = settings.IV_KEY          # must be 16 chars


def decrypt_aes(cipher_text: str) -> str:
    print(f"fasdfasd secret {SECRET_KEY}")
    print(f"fasdfasd IV {IV_KEY}")
    key = SECRET_KEY.encode("utf-8")
    iv = IV_KEY.encode("utf-8")

    encrypted_bytes = base64.b64decode(cipher_text)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_bytes)

    unpadded = unpad(decrypted, AES.block_size)

    return unpadded.decode("utf-8")