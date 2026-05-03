from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

SECRET_KEY = "&Rh)M#pCYN4vbtqMe$QxTtA6pFZ8n%@3"   # must match frontend
IV_KEY = "TttUa54x$UZMDXtT"           # must be 16 chars


def decrypt_aes(cipher_text: str) -> str:
    key = SECRET_KEY.encode("utf-8")
    iv = IV_KEY.encode("utf-8")

    encrypted_bytes = base64.b64decode(cipher_text)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_bytes)

    unpadded = unpad(decrypted, AES.block_size)

    return unpadded.decode("utf-8")