# src/photon_tools/model.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import numpy as np
import warnings

@dataclass(frozen=True)
class PhotonData:
    timestamps: np.ndarray
    detectors: Optional[np.ndarray] = None
    nanotimes: Optional[np.ndarray] = None
    timing_resolution: Optional[float] = None  # seconds per tick, e.g. 5e-9
    unit: str = "ticks"

    def __post_init__(self):
        if self.timing_resolution is not None:
            tr = float(self.timing_resolution)
            if tr <= 0:
                raise ValueError("timing_resolution must be > 0 seconds per tick")
            if tr < 1e-12 or tr > 1e-3:
                warnings.warn(
                    f"timing_resolution={tr} s looks unusual",
                    RuntimeWarning,
                )
            object.__setattr__(self, "timing_resolution", tr)

    @property
    def times_s(self) -> np.ndarray:
        if self.timing_resolution is None:
            raise ValueError(
                "timing_resolution is not set. "
                "Provide it when loading (e.g. pt.load(..., timing_resolution=5e-9)) "
                "or set ds.photons = ds.photons.with_timing_resolution(...)."
            )
        return self.timestamps * self.timing_resolution
    
    def by_detector(self) -> dict[int, np.ndarray]:
        """
        Split timestamps by detector channel.

        Returns
        -------
        dict[int, np.ndarray]
            Mapping detector_id -> timestamps (ticks).

        Raises
        ------
        ValueError if no detector information is present.
        """
        if self.detectors is None:
            raise ValueError("No detector information available")

        out: dict[int, np.ndarray] = {}
        for d in sorted(np.unique(self.detectors).tolist()):
            mask = self.detectors == d
            out[int(d)] = self.timestamps[mask]
        return out
    

@dataclass
class PhotonDataset:
    photons: PhotonData
    meta: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None
    source: Optional[str] = None