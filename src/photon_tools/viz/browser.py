from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd
import ipywidgets as widgets
from IPython.display import clear_output, display

from .. import load, load_ni_binary, preview


def browse_files(
    paths: Sequence[str | Path],
    *,
    results_path: str | Path = "screening_results.csv",
    default_bin_width_ms: float = 10.0,
    default_timing_resolution: float = 5e-9,
    width: int = 1050,
    height: int = 420,
    show_filename: bool = True,
):
    """
    Interactive Jupyter browser for visually screening many photon-counting files.

    - Next/Prev navigation
    - Keep checkbox + free-text note
    - Saves annotations to CSV
    - Uses Plotly legend to toggle detector channels
    - For files without suffix, assumes NI-binary and uses load_ni_binary.

    Returns
    -------
    ui : ipywidgets.VBox
        The widget container (already displayed).
    """

    paths = [Path(p) for p in paths]
    paths = [p for p in paths if p.exists()]
    if not paths:
        raise ValueError("No existing files provided to browse_files().")

    results_path = Path(results_path)

    # --- load or init annotations ---
    if results_path.exists():
        df = pd.read_csv(results_path)
    else:
        df = pd.DataFrame(columns=["path", "keep", "note", "bin_width_ms", "timing_resolution", "loader_hint"])
    df_index = {p: i for i, p in enumerate(df["path"].astype(str).tolist())}

    # --- widgets ---
    idx_slider = widgets.IntSlider(
        value=0, min=0, max=len(paths) - 1, step=1,
        description="File", continuous_update=False,
        layout=widgets.Layout(width="600px"),
    )
    btn_prev = widgets.Button(description="◀ Prev", layout=widgets.Layout(width="90px"))
    btn_next = widgets.Button(description="Next ▶", layout=widgets.Layout(width="90px"))

    bin_dd = widgets.Dropdown(
        options=[1, 2, 5, 10, 20, 50, 100],
        value=float(default_bin_width_ms),
        description="Bin (ms)",
        layout=widgets.Layout(width="220px"),
    )

    timing_txt = widgets.FloatText(
        value=float(default_timing_resolution),
        description="timing (s)",
        layout=widgets.Layout(width="260px"),
    )

    show_fn_chk = widgets.Checkbox(value=bool(show_filename), description="show filename in title", indent=False)
    keep_chk = widgets.Checkbox(value=False, description="KEEP", indent=False)

    note_txt = widgets.Textarea(
        value="", description="Note",
        layout=widgets.Layout(width="700px", height="90px"),
    )

    btn_save = widgets.Button(description="💾 Save", button_style="success")
    btn_save_next = widgets.Button(description="💾 Save & Next", button_style="success")

    status = widgets.HTML(value="")
    out = widgets.Output()

    # --- helpers ---
    def current_path() -> Path:
        return paths[idx_slider.value]

    def choose_loader(p: Path):
        if p.suffix == "":
            return load_ni_binary, "ni_binary"
        return None, ""

    def load_existing_annotation(p: Path):
        s = str(p)
        if s in df_index:
            row = df.iloc[df_index[s]]
            keep_chk.value = bool(row["keep"])
            note_txt.value = "" if pd.isna(row["note"]) else str(row["note"])
        else:
            keep_chk.value = False
            note_txt.value = ""

    def render():
        p = current_path()
        load_existing_annotation(p)

        with out:
            clear_output(wait=True)
            try:
                loader, hint = choose_loader(p)
                if loader is None:
                    ds = load(p, timing_resolution=float(timing_txt.value))
                else:
                    ds = load(p, loader=loader, timing_resolution=float(timing_txt.value))

                fig = preview(
                    ds,
                    bin_width_ms=float(bin_dd.value),
                    show_filename=bool(show_fn_chk.value),
                    width=width,
                    height=height,
                    show=False,
                )
                fig.show(config={"scrollZoom": True, "displaylogo": False})

                status.value = f"<b>{idx_slider.value+1}/{len(paths)}</b> — {p}"
            except Exception as e:
                status.value = f"<span style='color:#b00'><b>Error:</b> {e}</span><br>{p}"

    def save():
        nonlocal df, df_index
        p = current_path()
        loader, hint = choose_loader(p)

        record = {
            "path": str(p),
            "keep": bool(keep_chk.value),
            "note": note_txt.value,
            "bin_width_ms": float(bin_dd.value),
            "timing_resolution": float(timing_txt.value),
            "loader_hint": hint,
        }

        s = str(p)
        if s in df_index:
            df.loc[df_index[s], :] = record
        else:
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            df_index = {p: i for i, p in enumerate(df["path"].astype(str).tolist())}

        df.to_csv(results_path, index=False)
        status.value = status.value + " &nbsp;✅ saved"

    # --- handlers ---
    def clamp(i: int) -> int:
        return max(0, min(len(paths) - 1, i))

    def on_prev(_):
        idx_slider.value = clamp(idx_slider.value - 1)

    def on_next(_):
        idx_slider.value = clamp(idx_slider.value + 1)

    def on_save(_):
        save()

    def on_save_next(_):
        save()
        on_next(_)

    btn_prev.on_click(on_prev)
    btn_next.on_click(on_next)
    btn_save.on_click(on_save)
    btn_save_next.on_click(on_save_next)

    for w in [idx_slider, bin_dd, timing_txt, show_fn_chk]:
        w.observe(lambda change: render(), names="value")

    # --- layout ---
    controls_row1 = widgets.HBox([btn_prev, btn_next, idx_slider])
    controls_row2 = widgets.HBox([bin_dd, timing_txt, show_fn_chk, keep_chk])
    controls_row3 = widgets.HBox([btn_save, btn_save_next])

    ui = widgets.VBox([controls_row1, controls_row2, note_txt, controls_row3, status, out])
    display(ui)
    render()
    return ui