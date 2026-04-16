import subprocess, json, shutil, time
from pathlib import Path

ROOT = Path('.').resolve()
PY = str((ROOT / '.venv' / 'Scripts' / 'python.exe').resolve())
results = []

sfx = str(int(time.time()))
TV = f'tvalid_{sfx}:latest'
TNOCMD = f'tnocmd_{sfx}:latest'


def run_cmd(args):
    p = subprocess.run(args, capture_output=True, text=True)
    out = (p.stdout or '') + (p.stderr or '')
    return p.returncode, out


def add(name, ok, details):
    results.append({'name': name, 'passed': bool(ok), 'details': details})

# Ensure scratch base exists
from image_manager import load_manifest, save_manifest
try:
    load_manifest('scratch', 'latest')
except Exception:
    m = {'name':'scratch','tag':'latest','config':{'Env':[],'Cmd':[],'WorkingDir':'/'},'layers':[]}
    save_manifest('scratch', 'latest', m)

# temp contexts
ctx_root = ROOT / '.tmp_test_ctx'
if ctx_root.exists():
    shutil.rmtree(ctx_root)
ctx_root.mkdir(parents=True, exist_ok=True)

(ctx_root / 'no_docksmith').mkdir()

bad_instr = ctx_root / 'bad_instr'
bad_instr.mkdir()
(bad_instr / 'Docksmithfile').write_text('FROM scratch\nFOO bar\nCMD python main.py\n', encoding='utf-8')

missing_base = ctx_root / 'missing_base'
missing_base.mkdir()
(missing_base / 'Docksmithfile').write_text('FROM doesnotexist:latest\nCMD python main.py\n', encoding='utf-8')

no_cmd = ctx_root / 'no_cmd'
no_cmd.mkdir()
(no_cmd / 'Docksmithfile').write_text('FROM scratch\nWORKDIR /app\nCOPY . /app\nRUN echo built > built.txt\n', encoding='utf-8')
(no_cmd / 'main.py').write_text("print('hello')\n", encoding='utf-8')

# Valid flow
rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', TV, 'app', '--no-cache'])
add('build_cold_valid', rc == 0 and 'Successfully built' in out and '[CACHE MISS]' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', TV, 'app'])
add('build_warm_cache_hit', rc == 0 and '[CACHE HIT]' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'images'])
img_name = TV.split(':')[0]
ok = rc == 0 and 'NAME' in out and 'TAG' in out and 'ID' in out and 'CREATED' in out and img_name in out
add('images_list_valid', ok, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'run', TV])
add('run_default_valid', rc == 0 and 'App started' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'run', '-e', 'MODE=prod', TV])
add('run_env_override_valid', rc == 0 and 'ENV MODE = prod' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'run', TV, 'echo', 'OVERRIDE_OK'])
add('run_cmd_override_valid', rc == 0 and 'OVERRIDE_OK' in out, out[-700:])

# Invalid flow
rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', f'tnodock_{sfx}:latest', str(ctx_root / 'no_docksmith')])
add('build_invalid_missing_docksmithfile', rc != 0 and 'Docksmithfile not found' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', f'tbad_{sfx}:latest', str(bad_instr)])
add('build_invalid_unsupported_instruction', rc != 0 and 'Unsupported instruction on line 2' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', f'tmissbase_{sfx}:latest', str(missing_base)])
add('build_invalid_missing_base', rc != 0 and 'Base image not found in local store' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'run', f'image_not_exist_{sfx}:latest'])
add('run_invalid_missing_image', rc != 0 and 'Image not found:' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'build', '-t', TNOCMD, str(no_cmd)])
if rc == 0:
    rc2, out2 = run_cmd([PY, '-m', 'main', 'run', TNOCMD])
    add('run_invalid_no_cmd', rc2 != 0 and 'No CMD defined for image and no command override provided' in out2, out2[-700:])
else:
    add('run_invalid_no_cmd', False, 'Precondition build failed:\n' + out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'rmi', f'missing_for_rmi_{sfx}:latest'])
add('rmi_invalid_missing_image', rc != 0 and 'Image manifest not found' in out, out[-700:])

rc, out = run_cmd([PY, '-m', 'main', 'rmi', TNOCMD])
add('rmi_valid_existing_image', rc == 0 and 'Removed image manifest and layers' in out, out[-700:])

# runtime write isolation heuristic
host_file = ROOT / 'container_only.txt'
if host_file.exists():
    host_file.unlink()
rc, out = run_cmd([PY, '-m', 'main', 'run', TV, 'echo', 'x', '>', 'container_only.txt'])
add('runtime_isolation_write_check', rc == 0 and (not host_file.exists()), out[-700:] + f"\nhost_file_exists={host_file.exists()}")

# cleanup
try:
    shutil.rmtree(ctx_root)
except Exception:
    pass

summary = {
    'passed': sum(1 for r in results if r['passed']),
    'failed': sum(1 for r in results if not r['passed']),
    'total': len(results),
    'results': results,
}
Path('.tmp_test_results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({'passed': summary['passed'], 'failed': summary['failed'], 'total': summary['total']}, indent=2))
