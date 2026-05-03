import time

def is_expired(client_timestamp: int, window_ms: int = 60_000) -> bool:
    now_ms = int(time.time() * 1000)
    return abs(now_ms - client_timestamp) > window_ms