from .model import PhotonData, PhotonDataset
from .registry import load, load_many, register_loader, available_loaders

from .formats.photon_hdf5 import load_photon_hdf5
from .formats.spc import load_spc
from .formats.ni_binary_s1 import load_ni_binary

from .viz.preview import preview
from .viz.browser import browse_files

__all__ = [
    "PhotonData",
    "PhotonDataset",
    "load",
    "load_many",
    "register_loader",
    "available_loaders",

    "load_photon_hdf5",
    "load_spc",
    "load_ni_binary",

    "preview",
    "browse_files"
]

register_loader(".h5", ".hdf5", loader=load_photon_hdf5, overwrite=True)
register_loader(".spc", loader=load_spc, overwrite=True)
register_loader(".bin", loader=load_ni_binary, overwrite=True)



