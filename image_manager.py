import json
import os
import time
from config import IMAGES_DIR, LAYERS_DIR
from utils.hashing import sha256_bytes


def image_manifest_path(name: str, tag: str) -> str:
    fn = f"{name}_{tag}.json"
    return os.path.join(IMAGES_DIR, fn)


def save_manifest(name: str, tag: str, manifest: dict) -> str:
    data = json.dumps(manifest, sort_keys=True).encode('utf-8')
    digest = sha256_bytes(data)
    manifest['digest'] = f'sha256:{digest}'
    manifest['created'] = manifest.get('created') or time.strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(image_manifest_path(name, tag), 'w') as f:
        json.dump(manifest, f, indent=2)
    return manifest['digest']


def load_manifest(name: str, tag: str) -> dict:
    path = image_manifest_path(name, tag)
    if not os.path.exists(path):
        raise FileNotFoundError('Manifest not found')
    with open(path, 'r') as f:
        return json.load(f)


def list_images() -> list:
    out = []
    for fn in os.listdir(IMAGES_DIR):
        if fn.endswith('.json'):
            path = os.path.join(IMAGES_DIR, fn)
            try:
                with open(path, 'r') as f:
                    m = json.load(f)
                    name = m.get('name')
                    tag = m.get('tag')
                    digest = m.get('digest', '')
                    created = m.get('created', '')
                    out.append({'name': name, 'tag': tag, 'id': (digest.split(':',1)[1][:12] if ':' in digest else digest[:12]), 'created': created})
            except Exception:
                continue
    return out


def remove_image(name: str, tag: str):
    path = image_manifest_path(name, tag)
    if not os.path.exists(path):
        raise FileNotFoundError(f'Image manifest not found: {name}:{tag}')
    # load manifest and remove referenced layers
    with open(path, 'r') as f:
        m = json.load(f)
    layers = m.get('layers', [])
    for l in layers:
        d = l.get('digest', '')
        if d.startswith('sha256:'):
            hexs = d.split(':',1)[1]
            lp = layer_path(hexs)
            if os.path.exists(lp):
                os.remove(lp)
    os.remove(path)
    print(f'Removed image manifest and layers for {name}:{tag}')


def store_layer_bytes(digest: str, data: bytes) -> str:
    # digest is hex string; save as sha256_<digest>.tar
    fn = f'sha256_{digest}.tar'
    path = os.path.join(LAYERS_DIR, fn)
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            f.write(data)
    return path


def layer_path(digest: str) -> str:
    fn = f'sha256_{digest}.tar'
    return os.path.join(LAYERS_DIR, fn)
