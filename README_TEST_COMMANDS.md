# Docksmith Requirement Test Commands

This file lists the valid and invalid test commands executed against `requirement.txt` expectations.

## Environment setup

```powershell
.\.venv\Scripts\Activate.ps1
```

## Valid test cases

### 1) Build cold (no cache)

```powershell
python -m main build -t tvalid:latest app --no-cache
```

### 2) Build warm (cache expected)

```powershell
python -m main build -t tvalid:latest app
```

### 3) List images

```powershell
python -m main images
```

### 4) Run image using default CMD

```powershell
python -m main run tvalid:latest
```

### 5) Run image with ENV override

```powershell
python -m main run -e MODE=prod tvalid:latest
```

### 6) Run image with CMD override

```powershell
python -m main run tvalid:latest echo OVERRIDE_OK
```

### 7) Remove existing image

```powershell
python -m main rmi tnocmd:latest
```

### 8) Runtime host-write isolation heuristic check

```powershell
python -m main run tvalid:latest python -c "open('container_only.txt','w').write('x')"
```

Then verify on host that `container_only.txt` is not present in project root.

## Invalid test cases

### 9) Build with missing Docksmithfile

```powershell
python -m main build -t tnodock:latest .tmp_test_ctx/no_docksmith
```

### 10) Build with unsupported instruction

```powershell
python -m main build -t tbad:latest .tmp_test_ctx/bad_instr
```

### 11) Build with missing base image

```powershell
python -m main build -t tmissbase:latest .tmp_test_ctx/missing_base
```

### 12) Run non-existing image

```powershell
python -m main run image_not_exist:latest
```

### 13) Run image with no CMD and no override

```powershell
python -m main build -t tnocmd2:latest .tmp_no_cmd_case
python -m main run tnocmd2:latest
```

### 14) Remove non-existing image

```powershell
python -m main rmi missing_for_rmi:latest
```

## Optional helper command

A helper harness used during validation:

```powershell
.venv\Scripts\python.exe .\.tmp_run_req_tests.py
```
