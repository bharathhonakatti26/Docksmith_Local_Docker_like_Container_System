import json
import os
from config import CACHE_DIR

INDEX_PATH = os.path.join(CACHE_DIR, 'index.json')

def _load_index():
    if not os.path.exists(INDEX_PATH):
        return {}
    with open(INDEX_PATH, 'r') as f:
        return json.load(f)

def _save_index(idx):
    with open(INDEX_PATH, 'w') as f:
        json.dump(idx, f, indent=2)


def get_cached_layer(cache_key: str):
    idx = _load_index()
    return idx.get(cache_key)


def store_cached_layer(cache_key: str, digest: str):
    idx = _load_index()
    idx[cache_key] = digest
    _save_index(idx)
