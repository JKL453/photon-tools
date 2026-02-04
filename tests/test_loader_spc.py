from pathlib import Path
import photon_tools as pt

# test loading SPC with test data file
def test_load_spc_fixture(data_dir: Path):
    p = data_dir / "spc_min.spc"
    assert p.exists(), f"Missing test file: {p}"

    ds = pt.load(p)  # resolution usually from file
    assert ds.photons.timestamps.size > 0
    assert ds.photons.detectors is not None
    assert ds.photons.timing_resolution is not None