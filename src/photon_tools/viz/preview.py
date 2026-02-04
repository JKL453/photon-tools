from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from typing import Mapping, Sequence

from ..model import PhotonDataset



def _bin_timestamps(
    times_s: np.ndarray,
    bin_width_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Bin photon arrival times into a histogram.

    Returns
    -------
    t_centers : np.ndarray
        Time bin centers (seconds).
    counts : np.ndarray
        Counts per bin.
    """
    if times_s.size == 0:
        return np.array([]), np.array([])

    t_min = times_s.min()
    t_max = times_s.max()

    n_bins = int(np.ceil((t_max - t_min) / bin_width_s))
    if n_bins <= 0:
        return np.array([]), np.array([])

    edges = t_min + np.arange(n_bins + 1) * bin_width_s
    counts, _ = np.histogram(times_s, bins=edges)

    t_centers = edges[:-1] + 0.5 * bin_width_s
    return t_centers, counts


def preview(
    ds: PhotonDataset,
    *,
    bin_width_ms: float = 10.0,
    channels: Sequence[int] | None = None,
    detector_labels: Mapping[int, str] | None = None,
    max_points: int = 200_000,
    show_filename: bool = True,
    title: str | None = None,
    width: int | None = None,
    height: int | None = None,
    colors: Mapping[int, str] | None = None,
    line_width: float = 1.0,
    clamp_x_to_zero: bool = True,
    clamp_y_to_zero: bool = True,
    show: bool = True,
    show_config: dict | None = None,
):
    """
    Interactive preview of photon data using Plotly.

    Parameters
    ----------
    ds:
        PhotonDataset
    bin_width_ms:
        Bin width in milliseconds.
    channel:
        Detector channel to show (None = all photons).
    max_points:
        Maximum number of plotted points (decimation if needed).
    title:
        Optional plot title.
    """
    photons = ds.photons
    times_all = photons.times_s  # strict

    # --- determine channels ---
    if photons.detectors is None:
        channel_map = {None: times_all}
    else:
        all_channels = sorted(set(int(d) for d in photons.detectors))
        if channels is None:
            channels = all_channels

        channel_map = {ch: times_all[photons.detectors == ch] for ch in channels}

    bin_width_s = bin_width_ms * 1e-3

    fig = go.Figure()

    for ch, times_s in channel_map.items():
        t, y = _bin_timestamps(times_s, bin_width_s)

        # decimation
        if y.size > max_points:
            step = int(np.ceil(y.size / max_points))
            t = t[::step]
            y = y[::step]

        # --- name ---
        if ch is None:
            name = "all photons"
        else:
            if detector_labels and ch in detector_labels:
                name = detector_labels[ch]
            else:
                name = f"detector {ch}"

        # --- line styling (ALWAYS defined) ---
        line_kwargs = {"width": line_width}
        if colors and ch is not None and ch in colors:
            line_kwargs["color"] = colors[ch]

        fig.add_trace(
            go.Scattergl(
                x=t,
                y=y,
                mode="lines",
                name=name,
                line=line_kwargs,
            )
        )

    if title is None:
        parts = ["Photon trace", f"bin = {bin_width_ms} ms"]
        if show_filename and ds.source:
            parts.insert(1, Path(ds.source).name)
        title = " | ".join(parts)

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Counts / bin",
        width=width,
        height=height,
        legend=dict(title="Channel"),
        dragmode="pan",
    )

    if clamp_x_to_zero:
        fig.update_xaxes(rangemode="tozero")

    if clamp_y_to_zero:
        fig.update_yaxes(rangemode="tozero")

    if show:
        fig.show(
            config=show_config or {"scrollZoom": True, "displaylogo": False}
        )

    return fig