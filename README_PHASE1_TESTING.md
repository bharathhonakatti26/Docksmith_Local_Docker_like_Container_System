# Phase 1 Testing — Docksmith Core

This document walks through building and running a simple image using Docksmith Core.

Prerequisites
- WSL2 Ubuntu recommended for runtime isolation
- Python 3.10+
- `python -m venv .venv`
- `.\.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`

Example project layout (in same directory as Docksmith repository):
- app/
  - main.py
  - Docksmithfile

Example `Docksmithfile`:
```
FROM scratch
WORKDIR /app
ENV MODE=dev
COPY . /app
RUN echo Hello_from_RUN > hello.txt
CMD python main.py
```

Steps

1. Build the image

Cold build (skip cache lookups/writes):

```bash
python -m main build -t example:latest app --no-cache
```

Warm build (use cache):

```bash
python -m main build -t example:latest app
```

Expected output (examples):
- Per-step lines such as: `Step 4/6 : COPY . /app [CACHE MISS] 0.09s -> <digest>` or `... [CACHE HIT] 0.00s`.
- Final summary: `Successfully built sha256:<digest> example:latest (X.XXs)`

2. List images

```bash
python -m main images
```

Expected: a table header and one row per image, for example:

```
NAME                 TAG        ID           CREATED
example              latest     a1b2c3d4e5f6 2026-03-13T12:34:56Z
```
ID is the first 12 characters of the image manifest digest.

3. Run the image

Basic run:

```bash
python -m main run example:latest
```

Run with environment overrides (`-e` repeatable):

```bash
python -m main run -e MODE=prod example:latest
```

Run with CMD override (replaces image `CMD`):

```bash
python -m main run example:latest python -c "print('OVERRIDE')"
```

Expected:
- If running as root on Linux (WSL2): runtime will attempt `chroot` and execute inside the isolated FS.
- Otherwise the runtime prints a notice and executes the command with the extracted filesystem as the working directory.
- `-e KEY=VALUE` overrides are applied inside the container runtime.
- CMD override runs the supplied command instead of the image `CMD`.

4. Verify layer and manifest storage

Local storage layout (created by `config.py` at first run):

- `~/.docksmith/images/` — JSON manifests per image (named `<name>_<tag>.json`)
- `~/.docksmith/layers/` — content-addressed tar archives named `sha256_<digest>.tar`
- `~/.docksmith/cache/index.json` — build cache index (maps cache keys → layer digest)

5. Remove image

```bash
python -m main rmi example:latest
```

Expected: the image manifest is removed and all layer files referenced by that manifest are deleted from `~/.docksmith/layers/`.

Note: this implementation does not perform reference counting — if multiple images shared layers, those shared layer files will be removed when any image that referenced them is deleted.

Test scenarios

- Cold build vs warm build:
  - Run `build --no-cache` then `build` again; second run should show `[CACHE HIT]` for layer-producing steps.
- Modify a source file then rebuild:
  - Steps up to the change remain `[CACHE HIT]`; the changed step and subsequent steps show `[CACHE MISS]`.
- Runtime behavior:
  - `python -m main run example:latest` should print application output and show `ENV` values set by `ENV` or overridden by `-e`.
  - Files written by `RUN` during build (e.g., `hello.txt`) appear inside the container filesystem when running.
- Removal:
  - After `rmi`, confirm manifest file is removed from `~/.docksmith/images/` and the referenced `sha256_<digest>.tar` files are removed from `~/.docksmith/layers/`.

If you want, I can also update this README to include concrete expected output snippets captured from the example `app/` I added earlier.
