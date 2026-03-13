import requests
import os
import json
from image_manager import load_manifest, layer_path


def push_image(name: str, tag: str, server: str):
    # server is ip[:port]
    host = server if server.startswith('http') else f'http://{server}'
    manifest = load_manifest(name, tag)
    # upload layers
    for l in manifest.get('layers', []):
        d = l['digest'].split(':',1)[1]
        lp = layer_path(d)
        if not os.path.exists(lp):
            raise FileNotFoundError('Local layer missing: ' + lp)
        url = f"{host}/layers/{d}"
        with open(lp, 'rb') as f:
            print('Uploading layer', d)
            r = requests.post(url, data=f.read())
            r.raise_for_status()
    # upload manifest
    url = f"{host}/images"
    r = requests.post(url, json=manifest)
    r.raise_for_status()
    print('Pushed image', name, tag, 'to', server)
