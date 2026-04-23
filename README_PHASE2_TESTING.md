# Phase 2 Testing — Docksmith LAN (Two-machine step-by-step)

This checklist shows a clear step-by-step workflow to test Docksmith LAN using two machines on the same LAN.

Terminology
- Machine A: Builder + Registry (builds the image and hosts the registry)
- Machine B: Client (pulls images from the registry and runs them)

Prerequisites (both machines)
- Git clone this repository and activate a Python virtual environment
	- Linux / WSL2:
		```bash
		python3 -m venv .venv
		source .venv/bin/activate
		pip install -r requirements.txt
		```
	- Windows PowerShell:
		```powershell
		python -m venv .venv
		.\.venv\Scripts\Activate.ps1
		pip install -r requirements.txt
		```
- Ensure Machine B can reach Machine A on port 5000 (open firewall if needed).

Step 1 — Build image on Machine A
1. On Machine A prepare a build context (use the example `app/`):

```bash
# from repo root on Machine A
python -m main build -t myapp:latest ./app --no-cache
```

Expected output (cold build): per-step logs with `[CACHE MISS]` and a final line similar to:

```
Successfully built sha256:<digest> myapp:latest (0.12s)
```

Step 2 — Start registry on Machine A (listen on LAN)
1. Start the registry and keep it running (foreground or background):

```bash
# foreground
python -m main serve --host 0.0.0.0 --port 5000

# or background (Linux/WSL2)
nohup python -m main serve --host 0.0.0.0 --port 5000 &>/tmp/docksmith-registry.log &
```

2. Verify registry is reachable (from Machine A or B):

```bash
curl http://<A_IP>:5000/images
curl http://172.17.128.1:5000/images
# expected: [] or JSON list
```

Step 3 — Push image from Machine A to registry
1. Push the image you built to the registry (use Machine A's LAN IP `<A_IP>`):

```bash
python -m main push myapp:latest <A_IP>:5000
```

Expected:
- Logs showing `Uploading layer <digest>` for each layer
- `Pushed image myapp latest to <A_IP>:5000`
- Registry files appear under `~/.docksmith_registry/images/` and `~/.docksmith_registry/layers/` on Machine A

Step 3.5 — View and delete images in registry (Machine A or B)
1. View images currently stored in the registry:

```bash
python -m main registry-images <A_IP>:5000
```

Expected:
- Header `REGISTRY IMAGES` followed by lines like `myapp:latest`
- If empty: `No images found in registry`

2. Delete one image from the registry:

```bash
python -m main registry-rmi myapp:latest <A_IP>:5000
```

Expected:
- `Deleted registry image myapp:latest from <A_IP>:5000`

3. Verify deletion:

```bash
python -m main registry-images <A_IP>:5000
```

Expected:
- Deleted image no longer appears in registry list.

Step 4 — Pull image on Machine B
1. On Machine B (repo cloned and venv active), pull the image from Machine A:

```bash
python -m main pull myapp:latest <A_IP>:5000
```

Expected:
- Console shows `Downloading layer <digest>` for each layer
- On Machine B, manifests saved under `~/.docksmith/images/`, layers saved under `~/.docksmith/layers/`

Step 5 — Verify and run on Machine B
1. Verify the image is listed locally on Machine B:

```bash
python -m main images
```

Expected: table with `myapp latest <ID> <CREATED>`

2. Run the pulled image on Machine B:

```bash
# run normally
python -m main run myapp:latest

# run with env override
python -m main run -e MODE=prod myapp:latest

# run with CMD override
python -m main run myapp:latest python -c "print('OVERRIDE')"
```

Expected: the container's `CMD` runs and prints output on Machine B. If you run under WSL2 and as root (or have `unshare`), the runtime will use proper isolation; otherwise it will execute with extracted filesystem as working dir.

Verification: files written by the image during `RUN` should not appear in the host workspace (they should only be visible inside the container's extracted filesystem during runtime and in layer tar files under `~/.docksmith/layers/`).

Troubleshooting
- Connection refused when Machine B calls Machine A:
	- Confirm `<A_IP>` is correct (use `ipconfig` / `hostname -I`) and that port 5000 is open.
	- On Windows, allow inbound TCP 5000 in Windows Defender Firewall for the Python process.
- `curl` returns HTML or 404: ensure the registry server is the Docksmith Flask app and listening on the correct port.
- Push fails partway: check disk space on Machine A and inspect `~/.docksmith_registry/layers/` for partial files.
- Registry delete says image not found:
	- Verify exact tag/name with `python -m main registry-images <A_IP>:5000` and retry.

Advanced tests
- Simulate partial pulls: delete one layer file from `~/.docksmith_registry/layers/` on Machine A and attempt to `pull` on Machine B — the pull should fail with a clear error for missing layer.
- Test multiple clients: repeat Step 4/5 on additional machines on the LAN.

Cleanup
- Stop the registry on Machine A (`Ctrl+C` if foreground; kill background process otherwise).
- Remove pulled images on Machine B:

```bash
python -m main rmi myapp:latest
```

- Optionally remove image from registry on Machine A:

```bash
python -m main registry-rmi myapp:latest <A_IP>:5000
```

Notes
- The registry is intentionally simple (no auth/TLS). For LAN testing, this is acceptable, but do not expose it on untrusted networks.
- Registry storage: `~/.docksmith_registry/images/` and `~/.docksmith_registry/layers/` on Machine A.
