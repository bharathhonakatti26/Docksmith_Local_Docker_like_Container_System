import tempfile
import os
import sys
import shutil
import subprocess
import shlex
from image_manager import load_manifest, layer_path
from utils.tar_utils import extract_tar_bytes_to_dir, read_tar_file
from utils.isolation import run_in_isolation


def run_image(name: str, tag: str, cmd_override: list | None = None, env_overrides: dict | None = None):
    manifest = load_manifest(name, tag)
    cfg = manifest.get('config', {})
    env_list = cfg.get('Env', [])
    env = dict([e.split('=', 1) for e in env_list]) if env_list else {}
    if env_overrides:
        env.update(env_overrides)
    workdir = cfg.get('WorkingDir', '/')
    cmd = cfg.get('Cmd', [])
    if cmd_override is not None:
        cmd = cmd_override

    temp = tempfile.mkdtemp(prefix='docksmith_container_')
    try:
        # extract layers sequentially
        for l in manifest.get('layers', []):
            d = l['digest'].split(':', 1)[1]
            lp = layer_path(d)
            if os.path.exists(lp):
                extract_tar_bytes_to_dir(read_tar_file(lp), temp)
            else:
                raise FileNotFoundError(f'Layer file missing: {lp}')

        # prepare execution
        full_cmd = cmd if isinstance(cmd, list) else cmd
        if not full_cmd:
            # Fail clearly when no CMD provided and no override
            raise RuntimeError('No CMD defined for image and no command override provided')

        # Use shared isolation helper (unshare/chroot when available). Fallback to non-isolated run.
        # Platform-aware command string construction
        if isinstance(full_cmd, str):
            cmd_str = full_cmd
        else:
            # On Windows, use simple space-join; on Unix/Linux, use proper shell quoting
            if sys.platform == 'win32':
                cmd_str = ' '.join(str(c) for c in full_cmd)
            else:
                cmd_str = ' '.join(shlex.quote(str(c)) for c in full_cmd)
        print('Running command (isolation helper):', cmd_str)
        rc = run_in_isolation(temp, cmd_str, env=env, workdir=workdir or '/')
        if rc != 0:
            print(f'Process exited with code {rc}')
    finally:
        shutil.rmtree(temp)
