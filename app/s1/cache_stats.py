import atexit
import os
import time
from datetime import datetime
from collections import Counter

_error_types = Counter()

# Where the totals are written. Default: cache_stats.log in the folder you start S1 from.
LOG_FILE = os.getenv("CACHE_STATS_FILE", "cache_stats.log")
# Default: file is overwritten on every run. Set CACHE_STATS_APPEND=1 to keep old runs.
APPEND = os.getenv("CACHE_STATS_APPEND", "0") == "1"
# Set CACHE_STATS_PRINT=0 to silence the per-request console lines.
PRINT_EVENTS = os.getenv("CACHE_STATS_PRINT", "1") == "1"

FLUSH_EVERY = 1.0  # seconds between totals lines in the file

_counts = {
    "hits": 0,
    "misses": 0,
    "s2_fetches": 0,   # misses that actually called S2
    "coalesced": 0,    # misses that waited on another request's S2 call
    "redis_errors": 0,
}
_last_flush = 0.0

with open(LOG_FILE, "a" if APPEND else "w") as _f:
    _f.write(f"=== run started {datetime.now().isoformat(timespec='seconds')} ===\n")


def _line(tag: str = "") -> str:
    total = _counts["hits"] + _counts["misses"]
    rate = 100 * _counts["hits"] / total if total else 0.0
    return (
        f"{datetime.now().strftime('%H:%M:%S')} {tag}"
        f"hits={_counts['hits']} misses={_counts['misses']} "
        f"hit_rate={rate:.1f}% s2_fetches={_counts['s2_fetches']} "
        f"coalesced={_counts['coalesced']} redis_errors={_counts['redis_errors']}\n"
    )


def _write(tag: str = "") -> None:
    with open(LOG_FILE, "a") as f:
        f.write(_line(tag))
        if tag:  # only on the FINAL line
            for msg, n in _error_types.most_common():
                f.write(f"    {n} x {msg}\n")


def _bump(name: str, label: str, key: str) -> None:
    global _last_flush
    _counts[name] += 1
    if PRINT_EVENTS:
        print(f"{label}: {key}")
    now = time.monotonic()
    if now - _last_flush >= FLUSH_EVERY:
        _last_flush = now
        _write()


def record_hit(key: str) -> None:
    _bump("hits", "CACHE HIT", key)


def record_miss(key: str) -> None:
    _bump("misses", "CACHE MISS", key)


def record_s2_fetch(key: str) -> None:
    _bump("s2_fetches", "  -> S2 FETCH", key)


def record_coalesced(key: str) -> None:
    _bump("coalesced", "  -> COALESCED (waiting on in-flight fetch)", key)


def record_redis_error(op: str, exc: Exception) -> None:
    _counts["redis_errors"] += 1
    _error_types[f"{op} {type(exc).__name__}: {str(exc)[:80]}"] += 1


# final totals when the server stops
atexit.register(lambda: _write("FINAL "))