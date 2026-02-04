from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from ..model import PhotonData, PhotonDataset


def _correct_overflow_uint32_ticks(ar: np.ndarray) -> np.ndarray:
    """
    Correct uint32 overflow in a monotonically increasing tick counter.
    Returns int64 ticks.
    """
    ar = np.asarray(ar, dtype=np.uint32)
    overflow = np.zeros(ar.shape[0], dtype=np.int64)
    overflow[1:] = np.cumsum(ar[:-1] > ar[1:]).astype(np.int64)
    return ar.astype(np.int64) + overflow * (np.iinfo(np.uint32).max + 1)


def load_ni_binary(
    path: str | Path,
    *,
    timing_resolution: float = 10e-9,
    sort_by_time: bool = True,
) -> PhotonDataset:
    """
    Load custom NI binary format:
        little-endian uint32, shape (-1, 3): [tt_apd1, tt_apd2, tt_ttl]

    First two rows:
      - either [0,0,0] [0,0,0] (no TTL settings)
      - or TTL high/low in the TTL column (settings)

    If TTL is present:
      - ttl_settings = [ttl_high, ttl_low, ttl_cycle]
      - microtimes computed as ticks mod ttl_cycle (per APD)

    Returns a PhotonDataset with:
      - photons.timestamps: merged APD1+APD2 timestamps (ticks)
      - photons.detectors: 0 for APD1, 1 for APD2
      - photons.nanotimes: microtime within TTL cycle if available, else None
      - timing_resolution: seconds per tick (must be provided/known)
    """
    p = Path(path)

    data = np.fromfile(p, dtype="<u4")
    if data.size % 3 != 0:
        raise ValueError(f"File size not aligned to 3*uint32: {p}")

    data = data.reshape(-1, 3)
    tt_apd1 = data[:, 0]
    tt_apd2 = data[:, 1]
    tt_ttl = data[:, 2]

    if data.shape[0] < 2:
        raise ValueError(f"File too short: {p}")

    has_ttl_settings = not (tt_ttl[0] == 0 and tt_ttl[1] == 0)

    ttl_settings = None
    ttl_cycle = None

    # drop first two header rows
    tt_apd1 = tt_apd1[2:]
    tt_apd2 = tt_apd2[2:]
    tt_ttl_data = tt_ttl[2:]

    # keep only nonzero entries (events)
    apd1_raw = tt_apd1[tt_apd1 != 0]
    apd2_raw = tt_apd2[tt_apd2 != 0]

    apd1 = _correct_overflow_uint32_ticks(apd1_raw)
    apd2 = _correct_overflow_uint32_ticks(apd2_raw)

    ttl = None
    mt_apd1 = None
    mt_apd2 = None

    if has_ttl_settings:
        ttl_high = int(tt_ttl[0])
        ttl_low = int(tt_ttl[1])
        ttl_cycle = int(ttl_high + ttl_low)
        ttl_settings = np.array([ttl_high, ttl_low, ttl_cycle], dtype=np.int64)

        ttl_raw = tt_ttl_data[tt_ttl_data != 0]
        ttl = _correct_overflow_uint32_ticks(ttl_raw)

        # align start to TTL sync start (your original logic)
        if ttl.size >= 2:
            sync_start = ttl[0] - (ttl[1] - ttl[0])
        else:
            sync_start = ttl[0]

        apd1 = apd1 - sync_start
        apd2 = apd2 - sync_start
        ttl = ttl - sync_start

        # "microtime" within TTL cycle (not TCSPC, but useful)
        mt_apd1 = np.mod(apd1, ttl_cycle).astype(np.int64)
        mt_apd2 = np.mod(apd2, ttl_cycle).astype(np.int64)
    else:
        # align both channels to common offset (your original logic)
        if apd1.size and apd2.size:
            offset = min(apd1[0], apd2[0])
        elif apd1.size:
            offset = apd1[0]
        elif apd2.size:
            offset = apd2[0]
        else:
            offset = 0
        apd1 = apd1 - offset
        apd2 = apd2 - offset

    # merge channels into one stream + detectors array
    ts = np.concatenate([apd1, apd2]).astype(np.int64)
    det = np.concatenate(
        [np.zeros(apd1.size, dtype=np.int16), np.ones(apd2.size, dtype=np.int16)]
    )

    # optional nanotimes aligned to merged stream
    nt = None
    if mt_apd1 is not None and mt_apd2 is not None:
        nt = np.concatenate([mt_apd1, mt_apd2]).astype(np.int64)

    if sort_by_time and ts.size > 1:
        idx = np.argsort(ts)
        ts = ts[idx]
        det = det[idx]
        if nt is not None:
            nt = nt[idx]

    photons = PhotonData(
        timestamps=ts,
        detectors=det,
        nanotimes=nt,
        timing_resolution=float(timing_resolution),
    )

    meta: Dict[str, Any] = {
        "format": "ni-binary",
        "has_ttl": bool(has_ttl_settings),
        "ttl_settings": ttl_settings.tolist() if ttl_settings is not None else None,
        "nanotimes_kind": "ttl_phase_ticks" if nt is not None else None,
    }

    raw: Dict[str, Any] = {"path": str(p)}
    if ttl is not None:
        raw["ttl_timestamps"] = ttl  # careful: could be large; remove if you want lightweight raw

    return PhotonDataset(photons=photons, meta=meta, raw=raw, source=str(p))
