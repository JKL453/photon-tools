from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from ..model import PhotonData, PhotonDataset


def _pick_photon_group(h5: Any, group: Optional[str], group_index: int) -> str:
    """
    Pick a photon_data group.
    - If group is given (e.g. "photon_data0"), use it.
    - Else pick by index among groups starting with "photon_data".
    """
    if group is not None:
        if group not in h5:
            raise ValueError(f"Requested group '{group}' not found in file.")
        return group

    candidates = [k for k in h5.keys() if k.startswith("photon_data")]
    if not candidates:
        raise ValueError("No group starting with 'photon_data' found.")
    candidates = sorted(candidates)
    if group_index < 0 or group_index >= len(candidates):
        raise ValueError(f"group_index={group_index} out of range. Available: {candidates}")
    return candidates[group_index]


def load_photon_hdf5(
    path: str | Path,
    *,
    group: Optional[str] = None,
    group_index: int = 0,
    timing_resolution: float | None = None,
    include_comment: bool = True,
    keep_file_open: bool = False,
) -> PhotonDataset:
    """
    Load Photon-HDF5 file into a standardized PhotonDataset.

    Parameters
    ----------
    group:
        Explicit photon_data group name, e.g. "photon_data0".
    group_index:
        If group is None, choose the Nth photon_data* group (default 0).
    include_comment:
        If True, include /comment (decoded) in meta when present.
    keep_file_open:
        If True, keep the h5py.File handle in ds.raw (advanced usage).
        If False, close the file and store only lightweight raw info.

    Returns
    -------
    PhotonDataset
    """
    try:
        import h5py
    except ImportError as e:
        raise ImportError(
            "h5py is required to load Photon-HDF5. Install with: pip install h5py"
        ) from e

    p = Path(path)

    f = h5py.File(p, "r")
    try:
        photon_group = _pick_photon_group(f, group=group, group_index=group_index)

        # Your current code uses: photon_data0/timestamps and photon_data0/detectors
        g = f[photon_group]
        if "timestamps" not in g:
            raise ValueError(f"Dataset '{photon_group}/timestamps' not found.")

        timestamps = g["timestamps"][...].astype(np.int64, copy=False)

        detectors = None
        if "detectors" in g:
            detectors = g["detectors"][...]
            # detectors are usually small ints; keep as-is but ensure numpy array
            detectors = np.asarray(detectors, dtype=np.int8)

        nanotimes = None
        if "nanotimes" in g:
            nanotimes = np.asarray(g["nanotimes"][...])

        # Tick/unit handling: Photon-HDF5 can store timestamps_unit, etc.
        unit = "ticks"
        tick_ns = None

        # (Optional) look for common Photon-HDF5 fields
        # Keep it conservative: only set if present.
        # You can refine once we see your actual files.
        if "timestamps_specs" in g:
            ts_specs = g["timestamps_specs"]
            if "timestamps_unit" in ts_specs:
                raw_unit = ts_specs["timestamps_unit"][()]
                unit = raw_unit.decode() if hasattr(raw_unit, "decode") else str(raw_unit)

        photons = PhotonData(
            timestamps=timestamps,
            detectors=detectors,
            nanotimes=nanotimes,
            timing_resolution=timing_resolution,
            unit=unit,
        )

        meta: Dict[str, Any] = {
            "format": "photon-hdf5",
            "photon_group": photon_group,
            "groups": list(f.keys()),
        }

        if include_comment and "comment" in f:
            c = f["comment"][()]
            meta["comment"] = c.decode("utf-8", errors="replace") if hasattr(c, "decode") else str(c)

        # raw handling:
        # - default: don't keep file handle open (safer in notebooks)
        # - keep_file_open=True: store the open file object
        if keep_file_open:
            raw = f
            # IMPORTANT: if we keep it open, we must not close it below
            ds = PhotonDataset(photons=photons, meta=meta, raw=raw, source=str(p))
            return ds
        else:
            # store something lightweight that still helps debugging
            raw = {"path": str(p), "photon_group": photon_group}
            ds = PhotonDataset(photons=photons, meta=meta, raw=raw, source=str(p))
            return ds

    finally:
        if not keep_file_open:
            f.close()