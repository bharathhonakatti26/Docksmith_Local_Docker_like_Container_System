# Run instructions

1. Install dependencies (prefer inside WSL2 Ubuntu):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Basic CLI usage (from repo root):

```bash
# build image from current directory (contains Docksmithfile)
python -m main build -t myapp:latest .

# list images
python -m main images

# run image
python -m main run myapp:latest

# start registry server
python -m main serve --host 0.0.0.0 --port 5000
```

Notes:
- Run inside WSL2 for chroot-based isolation. If not root, runtime will execute without chroot but using extracted filesystem as working dir.
