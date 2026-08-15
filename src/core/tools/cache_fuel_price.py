"""
Persistent, rate-limit-aware cache for the German-fuel-price MCP server.

Design goals:
- Survives process restarts (MCP clients respawn the server often).
- Enforces the Tankerkönig rate limit (1 call / 5 min) across restarts.
- Serves stale data instead of blocking/erroring when the limit is active.
- Separate TTLs for station metadata (slow-changing) vs. prices (volatile).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Optional

from platformdirs import user_cache_dir

APP_NAME = "german-fuel-price-mcp"

PRICE_TTL_SECONDS = 5 * 60          # how long a price entry is considered fresh
STATION_TTL_SECONDS = 24 * 60 * 60  # station metadata changes rarely
MIN_CALL_INTERVAL_SECONDS = 5 * 60  # Tankerkönig rate limit

# --- geo key bucketing for the "list stations near location" search -------
#
# lat/lng are continuous, so two near-identical searches would never share
# a cache entry if we keyed on the raw floats. Instead we snap the center
# onto a grid and round the radius up to a fixed bucket, then PAD that
# radius enough to guarantee the snapped circle fully contains the caller's
# real requested circle (since snapping moves the center a little).
GRID_SIZE_DEG = 0.02  # ~2.2km per cell at German latitudes; tune for your use case
RADIUS_BUCKETS_KM = [5, 10, 15, 20, 25]  # Tankerkönig's usable range tops out at 25km
GRID_PADDING_KM = 2  # >= worst-case center shift from snapping (grid diagonal / 2)


def _snap_coord(value: float, grid: float = GRID_SIZE_DEG) -> float:
    return round(value / grid) * grid


def _snap_radius_up(radius_km: float) -> int:
    for bucket in RADIUS_BUCKETS_KM:
        if radius_km + GRID_PADDING_KM <= bucket:
            return bucket
    return RADIUS_BUCKETS_KM[-1]


def build_list_key(lat: float, lng: float, radius_km: float) -> str:
    """
    Canonical cache key for a 'list stations near location' search.

    Deliberately excludes fueltype and sort: neither changes which stations
    or prices come back from Tankerkönig (we always request type=all), so
    filtering/sorting happens client-side on a cache hit instead of forcing
    a fresh API call for every fueltype/sort combination.
    """
    lat_b = _snap_coord(lat)
    lng_b = _snap_coord(lng)
    radius_b = _snap_radius_up(radius_km)
    return f"list:{lat_b:.4f}:{lng_b:.4f}:{radius_b}"


@dataclass
class CacheEntry:
    data: Any
    fetched_at: float


class FuelPriceCache:
    """
    A single JSON-file-backed cache with a per-key TTL and a global
    last-call timestamp used to enforce the API rate limit.

    Not built for high-concurrency multi-process writes — if you expect
    several server instances hitting the same cache file simultaneously,
    swap the JSON file for SQLite (same interface, different backend).
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._dir = cache_dir or Path(user_cache_dir(APP_NAME))
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = self._dir / "cache.json"
        self._meta_path = self._dir / "meta.json"
        self._lock = Lock()
        self._store: dict[str, dict] = self._load(self._cache_path)
        self._meta: dict = self._load(self._meta_path)

    # ---------- low-level persistence ----------

    @staticmethod
    def _load(path: Path) -> dict:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self, path: Path, data: dict) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(path)  # atomic on POSIX and Windows

    # ---------- rate limiting ----------

    @property
    def _last_call(self) -> float:
        return self._meta.get("last_call", 0.0)

    def _record_call(self) -> None:
        self._meta["last_call"] = time.time()
        self._save(self._meta_path, self._meta)

    def seconds_until_call_allowed(self) -> float:
        elapsed = time.time() - self._last_call
        return max(0.0, MIN_CALL_INTERVAL_SECONDS - elapsed)

    # ---------- core get-or-fetch ----------

    def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl_seconds: int = PRICE_TTL_SECONDS,
    ) -> tuple[Any, bool]:
        """
        Returns (data, is_stale).

        - Fresh cache hit -> (data, False), no API call.
        - Expired cache but rate limit active -> (data, True), serves stale
          data rather than blocking or erroring.
        - Expired cache and rate limit clear -> calls fetch_fn(), refreshes
          the cache, returns (data, False).
        - No cache entry and rate limit active -> blocks until allowed
          (only happens on a cold cache for that key).
        """
        with self._lock:
            entry = self._store.get(key)
            now = time.time()
            is_fresh = entry is not None and (now - entry["fetched_at"]) < ttl_seconds

            if is_fresh:
                return entry["data"], False

            can_call = self.seconds_until_call_allowed() <= 0

            if not can_call:
                if entry is not None:
                    return entry["data"], True  # stale-while-rate-limited
                # No cached data at all yet for this key: nothing to serve.
                wait = self.seconds_until_call_allowed()
                time.sleep(wait)

            data = fetch_fn()
            self._record_call()
            self._store[key] = asdict(CacheEntry(data=data, fetched_at=time.time()))
            self._save(self._cache_path, self._store)
            return data, False

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._save(self._cache_path, self._store)


# ---------------------------------------------------------------------------
# Example usage inside an MCP tool handler
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cache = FuelPriceCache()

    def call_tankerkoenig_list(lat: float, lng: float, radius_km: float) -> dict:
        # Replace with the real Tankerkönig "list" call, always type=all.
        print(f"[API CALL] list stations near ({lat},{lng}) r={radius_km}km")
        return {
            "stations": [
                {"id": "abc-123", "dist": 1.2, "e5": 1.729, "e10": 1.679, "diesel": 1.599},
                {"id": "def-456", "dist": 3.8, "e5": 1.749, "e10": 1.699, "diesel": 1.609},
            ]
        }

    def search_stations(lat: float, lng: float, radius_km: float, fueltype: str = "e5", sort: str = "price"):
        key = build_list_key(lat, lng, radius_km)
        data, stale = cache.get_or_fetch(
            key,
            fetch_fn=lambda: call_tankerkoenig_list(lat, lng, radius_km),
            ttl_seconds=PRICE_TTL_SECONDS,
        )
        # Post-filter: the cached bucket may cover a larger radius than asked.
        stations = [s for s in data["stations"] if s["dist"] <= radius_km]
        stations.sort(key=(lambda s: s["dist"]) if sort == "dist" else (lambda s: s[fueltype]))
        if stale:
            for s in stations:
                s["_note"] = "served from cache, refresh rate-limited"
        return stations

    # Same location, different fueltype/sort -> same cache entry, no 2nd API call
    print(search_stations(52.5200, 13.4050, 5, fueltype="e5", sort="price"))
    print(search_stations(52.5200, 13.4050, 5, fueltype="diesel", sort="dist"))
    # Nearby but not identical coordinates, same radius bucket -> still a cache hit
    print(search_stations(52.5201, 13.4049, 5, fueltype="e10", sort="price"))
    # A genuinely different radius bucket (e.g. 3km) would be a real cache
    # miss here and correctly block/wait for the rate limit to clear - try
    # it and watch get_or_fetch enforce MIN_CALL_INTERVAL_SECONDS for real.