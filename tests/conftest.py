from __future__ import annotations
from pathlib import Path
import pytest

# set path to data dir to be able to use example data in all tests
@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"