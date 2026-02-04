from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional, Sequence

from .model import PhotonDataset

LoaderFn = Callable[[str | Path], PhotonDataset]

_REGISTRY: Dict[str, LoaderFn] = {}


def _norm_suffix(s: str) -> str:
    """Normalize suffix to a canonical form: '.h5', '.spc', ..."""
    s = s.strip().lower()
    if not s:
        raise ValueError("Empty suffix is not allowed")
    if not s.startswith("."):
        s = "." + s
    return s


def register_loader(*suffixes: str, loader: LoaderFn, overwrite: bool = False) -> None:
    """
    Register a loader function for one or more suffixes (e.g. '.h5', '.hdf5').

    Parameters
    ----------
    suffixes:
        One or more file suffixes.
    loader:
        Callable that takes a path and returns a PhotonDataset.
    overwrite:
        If False (default), raises if a suffix is already registered.
    """
    if loader is None:
        raise ValueError("loader must not be None")

    for s in suffixes:
        suf = _norm_suffix(s)
        if (not overwrite) and (suf in _REGISTRY):
            raise ValueError(f"Loader already registered for {suf}")
        _REGISTRY[suf] = loader


def available_loaders() -> Dict[str, LoaderFn]:
    """Return a copy of the currently registered loaders."""
    return dict(_REGISTRY)


def load(path: str | Path, *, loader: Optional[LoaderFn] = None, **kwargs) -> PhotonDataset:
    """
    Load a measurement file.

    - If `loader` is given: calls loader(path, **kwargs).
    - Otherwise selects a loader by file suffix from the internal registry.

    kwargs are forwarded to the loader.
    """
    p = Path(path)

    if loader is not None:
        return loader(p, **kwargs)

    suf = p.suffix.lower()
    if suf not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        raise ValueError(f"No loader registered for '{suf}'. Known suffixes: {known}")

    return _REGISTRY[suf](p, **kwargs)


def load_many(
    paths: Sequence[str | Path], *, loader: Optional[LoaderFn] = None, **kwargs
) -> list[PhotonDataset]:
    """
    Load many files. Convenience helper for notebooks.
    """
    return [load(p, loader=loader, **kwargs) for p in paths]