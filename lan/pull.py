import requests
import os
import json
from image_manager import store_layer_bytes, save_manifest
from config import LAYERS_DIR


def pull_image(name: str, tag: str, server: str):
    host = server if server.startswith('http') else f'http://{server}'
    url = f"{host}/images/{name}_{tag}"
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError('Manifest not found on registry')
    manifest = r.json()
    # download layers
    for l in manifest.get('layers', []):
        d = l['digest'].split(':',1)[1]
        url = f"{host}/layers/{d}"
        print('Downloading layer', d)
        rr = requests.get(url)
        rr.raise_for_status()
        store_layer_bytes(d, rr.content)
    # save manifest locally
    save_manifest(name, tag, manifest)
    print('Pulled image', name, tag, 'from', server)
