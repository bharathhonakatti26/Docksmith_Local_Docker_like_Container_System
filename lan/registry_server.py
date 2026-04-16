from flask import Flask, request, send_file, jsonify
import os
import json
from config import REGISTRY_DIR

app = Flask('docksmith_registry')
IMAGES_DIR = os.path.join(REGISTRY_DIR, 'images')
LAYERS_DIR = os.path.join(REGISTRY_DIR, 'layers')
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LAYERS_DIR, exist_ok=True)

@app.route('/layers/<digest>', methods=['POST'])
def upload_layer(digest):
    # store raw bytes
    path = os.path.join(LAYERS_DIR, f'sha256_{digest}.tar')
    with open(path, 'wb') as f:
        f.write(request.data)
    return ('', 201)

@app.route('/layers/<digest>', methods=['GET'])
def get_layer(digest):
    path = os.path.join(LAYERS_DIR, f'sha256_{digest}.tar')
    if not os.path.exists(path):
        return ('Not found', 404)
    return send_file(path, mimetype='application/octet-stream')

@app.route('/images', methods=['POST'])
def upload_image():
    manifest = request.get_json()
    if not manifest or 'name' not in manifest or 'tag' not in manifest:
        return ('bad request', 400)
    fn = f"{manifest['name']}_{manifest['tag']}.json"
    with open(os.path.join(IMAGES_DIR, fn), 'w') as f:
        json.dump(manifest, f, indent=2)
    return ('', 201)

@app.route('/images', methods=['GET'])
def list_images():
    out = []
    for fn in os.listdir(IMAGES_DIR):
        if fn.endswith('.json'):
            out.append(fn[:-5])
    return jsonify(out)

@app.route('/images/<name_tag>', methods=['GET'])
def get_image(name_tag):
    path = os.path.join(IMAGES_DIR, f'{name_tag}.json')
    if not os.path.exists(path):
        return ('Not found', 404)
    with open(path, 'r') as f:
        return jsonify(json.load(f))


@app.route('/images/<name_tag>', methods=['DELETE'])
def delete_image(name_tag):
    path = os.path.join(IMAGES_DIR, f'{name_tag}.json')
    if not os.path.exists(path):
        return ('Not found', 404)

    with open(path, 'r') as f:
        manifest = json.load(f)

    # Delete all layers referenced by this manifest (no reference counting).
    for layer in manifest.get('layers', []):
        digest = layer.get('digest', '')
        if isinstance(digest, str) and digest.startswith('sha256:'):
            hex_digest = digest.split(':', 1)[1]
            layer_path = os.path.join(LAYERS_DIR, f'sha256_{hex_digest}.tar')
            if os.path.exists(layer_path):
                os.remove(layer_path)

    os.remove(path)
    return ('', 204)


def run_server(host='0.0.0.0', port=5000):
    app.run(host=host, port=port)
