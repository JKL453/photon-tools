from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import phconvert

from ..model import PhotonData, PhotonDataset


def load_spc(
    path: str | Path,
    *,
    spc_model: str = "SPC-134",
    timing_resolution: float | None = None,
    sort_by_time: bool = False,
) -> PhotonDataset:
    """
    Load Becker & Hickl .spc files via phconvert.

    phconvert.bhreader.load_spc returns a tuple-like:
        [0] macrotime timestamps (tt)
        [1] routing/detector channel (0/1)
        [2] microtimes (mt)
        [3] macrotime resolution (seconds per tick)

    Parameters
    ----------
    timing_resolution:
        If given, overrides the value from the file.
    sort_by_time:
        If True, sort photons by timestamp (keeps detectors/nanotimes aligned).
        Usually not necessary, but can help if a file is not strictly ordered.

    Returns
    -------
    PhotonDataset
    """
    p = Path(path)
    data = phconvert.bhreader.load_spc(str(p), spc_model=spc_model)

    tt = np.asarray(data[0], dtype=np.int64)
    det = np.asarray(data[1], dtype=np.int16)
    mt = np.asarray(data[2]) if data[2] is not None else None

    file_res = float(data[3])  # seconds per tick
    res = float(timing_resolution) if timing_resolution is not None else file_res

    if sort_by_time and tt.size > 1:
        idx = np.argsort(tt)
        tt = tt[idx]
        det = det[idx]
        if mt is not None:
            mt = mt[idx]

    photons = PhotonData(
        timestamps=tt,
        detectors=det,
        nanotimes=mt,
        timing_resolution=res,
    )

    meta: Dict[str, Any] = {
        "format": "spc",
        "spc_model": spc_model,
        "timing_resolution_source": "override" if timing_resolution is not None else "file",
    }

    return PhotonDataset(photons=photons, meta=meta, raw={"path": str(p)}, source=str(p))