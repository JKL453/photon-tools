from pathlib import Path
import numpy as np
import pytest
import photon_tools as pt

# test loading photon HDF5 with test data file
def test_load_photon_hdf5_fixture(data_dir: Path):
    p = data_dir / "photon_hdf5_min.h5"
    assert p.exists(), f"Missing test file: {p}"

    # timing resolution in test data file is 5e-9
    ds = pt.load(p, timing_resolution=5e-9)

    assert ds.photons.timestamps.dtype.kind in ("i", "u")
    assert ds.photons.timestamps.ndim == 1
    assert ds.photons.timestamps.size > 0

    # detectors optional, but if present should align
    if ds.photons.detectors is not None:
        assert ds.photons.detectors.shape == ds.photons.timestamps.shape

    assert ds.photons.timing_resolution == 5e-9