import numpy as np
import pytest
from photon_tools.model import PhotonData

# timing resolution
def test_times_s_requires_timing_resolution():
    p = PhotonData(timestamps=np.array([0, 1, 2], dtype=np.int64))
    with pytest.raises(ValueError):
        _ = p.times_s

# time in seconds from timestamps and timing resolution
def test_times_s_computation():
    p = PhotonData(timestamps=np.array([0, 2, 4], dtype=np.int64), timing_resolution=5e-9)
    assert np.allclose(p.times_s, np.array([0, 10e-9, 20e-9]))

# split timestamps by detector
def test_by_detector():
    ts = np.array([10, 20, 30, 40], dtype=np.int64)
    det = np.array([0, 1, 0, 1], dtype=np.int16)
    p = PhotonData(timestamps=ts, detectors=det)
    out = p.by_detector()
    assert out[0].tolist() == [10, 30]
    assert out[1].tolist() == [20, 40]

# test for multiple detectors
def test_multi_detector():
    ts = np.arange(10)
    det = np.array([0,1,2,3,0,1,2,3,0,1])
    p = PhotonData(timestamps=ts, detectors=det)
    out = p.by_detector()
    assert set(out.keys()) == {0,1,2,3}