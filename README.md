# photon-tools

Lightweight Python tools for loading, inspecting, and screening single-molecule photon counting data.

`photon-tools` is designed for **interactive, notebook-based workflows** commonly used in single-molecule fluorescence experiments.  
The focus is on **data loading, standardization, and visual inspection**, not on enforcing a specific analysis pipeline.

---

## Motivation

In single-molecule experiments, especially with photon-counting data:

- data quality often **cannot be judged from scalar metrics alone**
- visual inspection of time traces is essential (blinking, drift, artifacts, IR effects, etc.)
- experiments typically produce **many measurement files** that must be screened efficiently

`photon-tools` provides:
- a clean and extensible **data loading layer**
- a **standardized in-memory data model**
- fast, interactive **Plotly-based previews**
- a **Jupyter-based browser** for screening and annotating many files

---

## Features

### ✔ Data loading
- Built-in loader for **Photon-HDF5**
- Unified data representation via `PhotonDataset` / `PhotonData`
- Optional runtime registration of **custom loaders** (no forking required)

### ✔ Clean data model
- Integer timestamps (ticks)
- Optional detector/channel information
- Explicit `timing_resolution` (seconds per tick)
- Safe conversion to physical time
- Easy splitting by detector channel

### ✔ Interactive preview (Plotly)
- Fast binning of large photon streams
- Multiple detector channels in one plot
- Clickable legend to enable/disable channels
- Scroll-wheel zoom + mouse pan
- Physically meaningful defaults (axes clamped to zero)
- Fully customizable via returned Plotly `Figure`

### ✔ Screening workflow (Jupyter)
- Browse many files interactively
- Next / Previous navigation
- Visual evaluation instead of purely numeric filtering
- Mark files as *keep / reject*
- Store annotations and notes in a CSV file

---

## Installation

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

Install in editable (development) mode:

```bash
pip install -e .
```

Required dependencies:
- numpy
- h5py
- plotly
- nbformat

For the notebook browser:
```bash
pip install ipywidgets pandas
```

---

## Basic Usage

### Load a Photon-HDF5 file



```python
import photon_tools as pt

ds = pt.load(
    "measurement.hdf5",
    timing_resolution=5e-9,  # seconds per tick
)
```

### Access data

```python
ds.photons.timestamps        # raw integer timestamps (ticks)
ds.photons.times_s           # physical time in seconds
ds.photons.detectors         # detector/channel IDs
```

Split by detector channel:

```python
by_ch = ds.photons.by_detector()
t_ch0 = by_ch[0]
t_ch1 = by_ch[1]
```

---

## Interactive Preview

Quick visual inspection of a time trace:

```python
pt.preview(ds, bin_width_ms=10)
```

Customize appearance and detector labels:

```python
pt.preview(
    ds,
    bin_width_ms=5,
    detector_labels={0: "donor", 1: "acceptor"},
    colors={0: "royalblue", 1: "firebrick"},
    width=1000,
    height=400,
)
```

Further customization via Plotly:

```python
fig = pt.preview(ds, show=False)
fig.update_yaxes(type="log")
fig.show(config={"scrollZoom": True})
```

Because `preview()` returns a Plotly `Figure`, all Plotly features remain available.

---

## Screening Many Files (Notebook Browser)

A ready-to-use **Jupyter notebook example** for interactive file screening is provided in:

```
notebooks/02_browse_files.ipynb
```
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/<USER>/<REPO>/main?labpath=notebooks%2F02_screening_browser.ipynb)

The browser allows you to:
- step through many measurement files
- inspect traces interactively (zoom, pan, toggle channels)
- mark files as *keep* or *reject*
- add free-text notes
- store all annotations in a CSV file

This workflow is intended for **expert-driven screening**, where visual judgment is essential and cannot be replaced by scalar metrics alone.

---

## Custom Loaders

Custom file formats can be supported without modifying or forking the package.

Define a loader function and register it at runtime:

```python
def my_loader(path):
    ...
    return PhotonDataset(...)
```

```python
pt.register_loader(".dat", loader=my_loader)
ds = pt.load("custom_format.dat")
```

This allows extending `photon-tools` in notebooks or scripts in a lightweight and flexible way.

---

## Files without extensions

Some binary formats (e.g. custom NI time-tagged data) do not use file extensions.
In this case, the loader must be specified explicitly:

```python
ds = pt.load(
    "measurement_001",
    loader=pt.load_ni_binary,
    timing_resolution=10e-9,
)
```

---

## Design Philosophy

- **Notebook-first**
- **Explicit over implicit**
- **No silent assumptions**
- **Visual inspection before automation**
- Keep the core lightweight; downstream analysis is user-specific

`photon-tools` is not an analysis framework — it is a **foundation** for interactive and exploratory workflows.

---

## Status

This project is under active development and tailored to real experimental workflows.  
APIs may evolve, but changes are made conservatively and with practical use cases in mind.

---

## License

(Choose one, e.g. MIT or BSD-3-Clause)