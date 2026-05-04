from fastapi import Request, HTTPException, Depends
from app.utils.aes import decrypt_aes
from app.utils.time import is_expired


async def decrypt_request(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    request_id = body.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="Missing request_id")

    try:
        decrypted = decrypt_aes(request_id)
        print(f"decrypted :{decrypted}")
        ts_str, nonce = decrypted.split(":")
        timestamp = int(ts_str)

    except ValueError as e:
        print("Error :",e)
        raise HTTPException(status_code=400, detail="Invalid request_id")
    except Exception as e:
        print("Error :",e)
        raise HTTPException(status_code=400, detail="Invalid request_id")

    if is_expired(timestamp):
        raise HTTPException(status_code=400, detail="request_id expired")

    # ✅ validation only (no return data needed)
    return True