import json
import os
import random
import yaml
import numpy as np
import pandas as pd


def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _convert(o):
    """Recursively convert objects to JSON-serializable types."""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    if isinstance(o, dict):
        return {k: _convert(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_convert(v) for v in o]
    return o


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    safe_data = _convert(data)
    with open(path, "w") as f:
        json.dump(safe_data, f, indent=2)


def set_seeds(seed=42):
    random.seed(seed)
    np.random.seed(seed)
