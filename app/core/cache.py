"""
Simple in-process TTL cache — không cần Redis, phù hợp single-process.
Dùng cho: danh sách nhân viên, danh sách công ty (đọc nhiều, ghi ít).
"""
import time
import threading
from typing import Any, Optional

_store: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
_lock = threading.Lock()


def cache_get(key: str) -> Optional[Any]:
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if time.monotonic() > expire_at:
            del _store[key]
            return None
        return value


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    with _lock:
        _store[key] = (value, time.monotonic() + ttl)


def cache_delete(key: str) -> None:
    with _lock:
        _store.pop(key, None)


def cache_delete_prefix(prefix: str) -> None:
    """Xoá tất cả key bắt đầu bằng prefix — dùng khi có write."""
    with _lock:
        to_delete = [k for k in _store if k.startswith(prefix)]
        for k in to_delete:
            del _store[k]
