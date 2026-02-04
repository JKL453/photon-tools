from pathlib import Path
import numpy as np
import pytest
from photon_tools.formats.ni_binary_s1 import load_ni_binary

def _assert_basic(ds):
    assert ds.photons.timestamps.ndim == 1
    assert ds.photons.timestamps.size > 0
    assert ds.photons.detectors is not None
    assert ds.photons.detectors.shape == ds.photons.timestamps.shape
    # should only contain detector IDs 0/1 for your format
    assert set(np.unique(ds.photons.detectors).tolist()).issubset({0, 1})

def test_load_ni_binary_no_ttl(data_dir: Path):
    p = data_dir / "ni_no_ttl_min"
    assert p.exists(), f"Missing test file: {p}"

    ds = load_ni_binary(p, timing_resolution=10e-9)
    _assert_basic(ds)

"""
def test_load_ni_binary_with_ttl(data_dir: Path):
    p = data_dir / "ni_with_ttl_min"
    assert p.exists(), f"Missing test file: {p}"

    ds = load_ni_binary(p, timing_resolution=10e-9)
    _assert_basic(ds)

    assert ds.meta.get("has_ttl") is True
    # nanotimes exist for TTL variant in our suggested loader
    # (if you implemented it differently, adjust this)
    assert ds.photons.nanotimes is not None
    assert ds.photons.nanotimes.shape == ds.photons.timestamps.shape
"""