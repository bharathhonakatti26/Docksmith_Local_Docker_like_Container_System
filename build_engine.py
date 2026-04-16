import os
import shutil
import tempfile
import json
from utils.tar_utils import create_tar_from_dir
from utils.hashing import sha256_bytes, sha256_file
from image_manager import store_layer_bytes, save_manifest, layer_path, load_manifest
from cache_manager import get_cached_layer, store_cached_layer
from config import LAYERS_DIR
from utils.isolation import run_in_isolation


ALLOWED = {'FROM', 'COPY', 'RUN', 'WORKDIR', 'ENV', 'CMD'}


def parse_docksmithfile(path: str) -> list:
    instrs = []
    with open(path, 'r') as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(maxsplit=1)
            cmd = parts[0].upper()
            if cmd not in ALLOWED:
                raise ValueError(f'Unsupported instruction on line {lineno}: {cmd}')
            arg = parts[1] if len(parts) > 1 else ''
            instrs.append((cmd, arg))
    return instrs


def _compute_copy_src_hashes(context: str, src: str) -> str:
    srcpath = os.path.join(context, src)
    entries = []
    if os.path.isdir(srcpath):
        for root, dirs, files in os.walk(srcpath):
            dirs.sort()
            files.sort()
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, start=srcpath)
                h = sha256_file(full)
                entries.append((rel.replace('\\', '/'), h))
    elif os.path.exists(srcpath):
        h = sha256_file(srcpath)
        entries.append((os.path.basename(srcpath), h))
    entries.sort()
    return json.dumps(entries, separators=(',', ':'), sort_keys=True)


def build_image(context: str, name: str, tag: str, no_cache: bool=False):
    """Builds image from a Docksmithfile in `context`.

    This implements a simple layer model: COPY and RUN produce layers.
    Each layer is a tar archive whose sha256 bytes digest is used as identifier.
    A deterministic cache is used to skip work when possible.
    """
    ds_path = os.path.join(context, 'Docksmithfile')
    if not os.path.exists(ds_path):
        raise FileNotFoundError('Docksmithfile not found in context')
    instrs = parse_docksmithfile(ds_path)

    workdir = ''
    env = {}
    layers = []
    prev_digest = ''
    cache_broken = False

    import time
    total_start = time.time()
    step_idx = 0
    for cmd, arg in instrs:
        step_idx += 1
        step_label = f"Step {step_idx}/{len(instrs)} : {cmd} {arg}"
        step_start = time.time()
        if cmd == 'FROM':
            base = arg.strip()
            if not base:
                raise ValueError('FROM requires a base image name, e.g. FROM alpine:3.18')
            bname, btag = (base.split(':', 1) if ':' in base else (base, 'latest'))
            try:
                bm = load_manifest(bname, btag)
            except FileNotFoundError as exc:
                raise FileNotFoundError(
                    f'Base image not found in local store: {bname}:{btag}'
                ) from exc
            prev_digest = bm.get('digest', '').split(':', 1)[1] if 'digest' in bm else ''
            duration = time.time() - step_start
            print(f"{step_label} (info) {duration:.2f}s")
            continue
        if cmd == 'WORKDIR':
            workdir = arg
            duration = time.time() - step_start
            print(f"{step_label} (config) {duration:.2f}s")
            continue
        if cmd == 'ENV':
            key, val = arg.split('=', 1)
            env[key] = val
            duration = time.time() - step_start
            print(f"{step_label} (config) {duration:.2f}s")
            continue
        if cmd == 'CMD':
            cmd_cfg = arg.strip().split()
            duration = time.time() - step_start
            print(f"{step_label} (config) {duration:.2f}s")
            continue
        if cmd == 'COPY':
            # arg: "src dest"
            src, dest = arg.split()
            src_hashes = _compute_copy_src_hashes(context, src)
            cache_key = sha256_bytes((prev_digest + 'COPY' + arg + workdir + json.dumps(env, sort_keys=True) + src_hashes).encode('utf-8'))
            cached = None if no_cache or cache_broken else get_cached_layer(cache_key)
            if cached and os.path.exists(layer_path(cached)):
                layers.append({'digest': f'sha256:{cached}'})
                prev_digest = cached
                duration = time.time() - step_start
                print(f"{step_label} [CACHE HIT] {duration:.2f}s")
                continue
            # create temp dir with files copied into dest
            with tempfile.TemporaryDirectory() as td:
                target = os.path.join(td, dest.lstrip('/'))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                srcpath = os.path.join(context, src)
                if os.path.isdir(srcpath):
                    shutil.copytree(srcpath, target)
                else:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    shutil.copy2(srcpath, target)
                tar_bytes = create_tar_from_dir(td)
                digest = sha256_bytes(tar_bytes)
                store_layer_bytes(digest, tar_bytes)
                layers.append({'digest': f'sha256:{digest}'})
                if not no_cache:
                    store_cached_layer(cache_key, digest)
                prev_digest = digest
                duration = time.time() - step_start
                print(f"{step_label} [CACHE MISS] {duration:.2f}s -> {digest}")
                cache_broken = True
            continue
        if cmd == 'RUN':
            # Simple strategy: materialize previous layers into tempdir, run the command, then tar full FS
            cache_key = sha256_bytes((prev_digest + 'RUN' + arg + workdir + json.dumps(env, sort_keys=True)).encode('utf-8'))
            cached = None if no_cache or cache_broken else get_cached_layer(cache_key)
            if cached and os.path.exists(layer_path(cached)):
                layers.append({'digest': f'sha256:{cached}'})
                prev_digest = cached
                duration = time.time() - step_start
                print(f"{step_label} [CACHE HIT] {duration:.2f}s")
                continue
            with tempfile.TemporaryDirectory() as td:
                # extract previous layers if any
                for l in layers:
                    d = l['digest'].split(':', 1)[1]
                    lp = layer_path(d)
                    if os.path.exists(lp):
                        from utils.tar_utils import extract_tar_bytes_to_dir, read_tar_file
                        extract_tar_bytes_to_dir(read_tar_file(lp), td)
                # run the command in td using the isolation helper
                print('Running command in temp FS:', arg)
                rc = run_in_isolation(td, arg, env=env, workdir=workdir or '/')
                if rc != 0:
                    print(f'RUN command exited with code {rc}')
                tar_bytes = create_tar_from_dir(td)
                digest = sha256_bytes(tar_bytes)
                store_layer_bytes(digest, tar_bytes)
                layers.append({'digest': f'sha256:{digest}'})
                if not no_cache:
                    store_cached_layer(cache_key, digest)
                prev_digest = digest
                duration = time.time() - step_start
                print(f"{step_label} [CACHE MISS] {duration:.2f}s -> {digest}")
                cache_broken = True
            continue

    # build manifest
    manifest = {
        'name': name,
        'tag': tag,
        'config': {
            'Env': [f'{k}={v}' for k, v in env.items()],
            'Cmd': cmd_cfg if 'cmd_cfg' in locals() else [],
            'WorkingDir': workdir
        },
        'layers': layers
    }
    total_duration = time.time() - total_start
    digest = save_manifest(name, tag, manifest)
    print(f"Successfully built {digest} {name}:{tag} ({total_duration:.2f}s)")
    return digest
