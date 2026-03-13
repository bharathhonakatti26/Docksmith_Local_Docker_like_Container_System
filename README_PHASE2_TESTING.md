# Phase 2 Testing — Docksmith LAN

This guide shows how to start the registry, push an image from one host, pull it on another, and run it.

Prerequisites
- Registry and clients should run on machines reachable on the LAN (or use multiple WSL2 instances with bridged networking)
- `pip install -r requirements.txt`

1. Start the registry server

```bash
python -m main serve --host 0.0.0.0 --port 5000
```

Expected: Flask server listening; `GET /images` returns `[]` initially.

2. Push an image to the registry

On Developer A (who has built an image `example:latest`):

```bash
python -m main push example:latest 192.168.1.10:5000
```

Expected:
- Layers uploaded (logs show "Uploading layer <digest>")
- Manifest uploaded

3. Pull the image from another host

On Developer B:

```bash
python -m main pull example:latest 192.168.1.10:5000
```

Expected:
- Downloads layers to `~/.docksmith/layers/`
- Stores manifest in `~/.docksmith/images/`

4. Run pulled image

```bash
python -m main run example:latest
```

Expected: `CMD` runs as in Phase 1 run instructions.

API Endpoints
- `POST /layers/<digest>` — upload raw layer tar bytes
- `GET /layers/<digest>` — download raw layer tar bytes
- `POST /images` — upload manifest JSON
- `GET /images` — list images
- `GET /images/<name>_<tag>` — retrieve manifest JSON

Test scenarios
- Push large image with multiple layers and verify all layers present on registry.
- Pull partially (simulate missed layer) and ensure error handling is clear.

Notes
- The registry stores data in `~/.docksmith_registry/` under `images/` and `layers/`.
- Authentication, TLS, and advanced registry features are intentionally omitted in this educational prototype.
