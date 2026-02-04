import numpy as np
from photon_tools.model import PhotonData, PhotonDataset
from photon_tools.viz.preview import preview

def test_preview_returns_figure():
    photons = PhotonData(
        timestamps=np.array([0, 1, 2, 10, 11], dtype=np.int64),
        detectors=np.array([0, 0, 1, 1, 0], dtype=np.int16),
        timing_resolution=1e-6,
    )
    ds = PhotonDataset(photons=photons, meta={}, raw=None, source="x")
    fig = preview(ds, show=False)
    assert fig is not None
    assert len(fig.data) >= 1