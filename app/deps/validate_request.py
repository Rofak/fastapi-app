from fastapi import Request, HTTPException, Depends
import time
import hmac
import hashlib
import json
from app.utils.aes import decrypt

SECRET_KEY = b"super-secret-key"

# replace with Redis in production
used_signatures = set()


def generate_signature(payload: dict, timestamp: int) -> str:
    message = json.dumps(payload, sort_keys=True) + str(timestamp)
    return hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()


async def validate_request(request: Request):
    body = await request.json()

    timestamp = body.get("timestamp")
    signature = body.get("signature")

    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Missing timestamp or signature")

    # ⏱️ prevent replay (expired request)
    now = int(time.time())
    if abs(now - int(timestamp)) > 60:
        raise HTTPException(status_code=400, detail="Request expired")

    # 🔐 rebuild expected signature
    payload = body.copy()
    payload.pop("signature", None)

    expected = generate_signature(payload, timestamp)

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 🚫 prevent duplicate (replay attack)
    if signature in used_signatures:
        raise HTTPException(status_code=409, detail="Duplicate request")

    used_signatures.add(signature)

    return True

async def decrypt_request(request: Request):
    body = await request.json()

    token = body.get("request_id")
    if not token:
        raise HTTPException(400, "Missing payload")

    try:
        decrypted = decrypt(token)
        data = json.loads(decrypted)
    except Exception:
        raise HTTPException(400, "Invalid encrypted payload")

    # attach to request.state
    request.state.decrypted = data

    return data