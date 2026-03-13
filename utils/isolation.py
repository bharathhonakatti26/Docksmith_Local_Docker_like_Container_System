import shutil
import subprocess
import os


def _has_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run_in_isolation(root: str, command: str, env: dict | None = None, workdir: str = '/') -> int:
    """Run a shell command inside an isolated environment rooted at `root`.

    Tries, in order:
    - If `unshare` is available: `unshare --fork --pid --mount-proc chroot root sh -lc command`
    - If running as root (geteuid==0): `chroot root sh -lc command`
    - Otherwise: fallback to running command in working directory under `root` (no isolation).

    Returns the subprocess exit code.
    """
    env = env or {}
    # prefer unshare when available
    if _has_command('unshare'):
        cmd = ['unshare', '--fork', '--pid', '--mount-proc', 'chroot', root, 'sh', '-lc', command]
        return subprocess.run(cmd, env={**os.environ, **env}).returncode

    # try chroot if available (and on Unix)
    geteuid = getattr(os, 'geteuid', None)
    if callable(geteuid):
        try:
            if geteuid() == 0 and _has_command('chroot'):
                cmd = ['chroot', root, 'sh', '-lc', command]
                return subprocess.run(cmd, env={**os.environ, **env}).returncode
        except Exception:
            pass

    # fallback: run without isolation in a subprocess with cwd inside root
    cwd_path = os.path.join(root, workdir.lstrip('/')) if workdir != '/' else root
    os.makedirs(cwd_path, exist_ok=True)
    return subprocess.run(command, shell=True, cwd=cwd_path, env={**os.environ, **env}).returncode

