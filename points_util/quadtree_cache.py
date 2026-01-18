from __future__ import annotations
from pathlib import Path
import pickle
import os
import time


def save_quadtree(tree, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(tree, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_quadtree(path: str | Path):
    path = Path(path)
    with path.open("rb") as f:
        return pickle.load(f)

