Project Title

Docksmith LAN: A Hybrid Local-Network Container Platform

Project Goal

Build a mini Docker-like container platform in Python called Docksmith.

The system must support two phases:

Phase 1 — Docksmith Core

A single-machine container build and runtime system that works completely offline.

Phase 2 — Docksmith LAN

An extension allowing developers on the same Local Area Network (LAN) to share container images without rebuilding them.

This system mimics Docker + Docker Registry, but restricted to a local network environment.

Host Environment

Development environment:

Host OS:
Windows 10 / Windows 11

Linux environment for container isolation:
Ubuntu via WSL2

Reason:
Container isolation relies on Linux primitives such as:

chroot

namespaces

filesystem isolation
Docksmith LAN — Hybrid Container Platform

This repository contains a working starter implementation for Docksmith: a minimal Docker-like image build/runtime system (Phase 1) and a small LAN registry server + push/pull clients (Phase 2).

Key files created in this workspace:

- `main.py` and `cli.py` — CLI entry and commands
- `build_engine.py` — Docksmithfile parser and build pipeline
- `runtime.py` — simple container runtime (extracts layers and runs `CMD`)
- `image_manager.py` / `cache_manager.py` — manifest and cache handling
- `utils/hashing.py`, `utils/tar_utils.py` — helpers for SHA256 and tar bytes
- `lan/registry_server.py`, `lan/push.py`, `lan/pull.py` — LAN registry and clients
- `config.py` — local storage paths for images/layers/cache
- `requirements.txt` — Python dependencies

The implementation is intentionally minimal and focuses on correctness and clarity for educational purposes. It is structured so Phase 1 (build + run) works independently even if the LAN registry is not running.

Run instructions and testing steps are provided in separate files:

- `README_RUN.md` — how to install dependencies and run the system
- `README_PHASE1_TESTING.md` — step-by-step testing for Docksmith Core
- `README_PHASE2_TESTING.md` — step-by-step testing for Docksmith LAN (registry, push, pull)

Notes and limitations:
- The runtime will attempt to use `chroot` only when executed as root; otherwise it runs the image `CMD` with the extracted filesystem as the working directory.
- Layer generation for `RUN` instructions materializes the whole filesystem into a temp directory and tars it after executing the command.
- This design favors simplicity and reproducibility for teaching the layer/cache concepts.

See `README_PHASE1_TESTING.md` and `README_PHASE2_TESTING.md` for concrete test scenarios and expected outputs.