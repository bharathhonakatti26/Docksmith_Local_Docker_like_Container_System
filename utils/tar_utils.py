import tarfile
import io
import os
from typing import List


def _normalize_tarinfo(ti: tarfile.TarInfo):
    # zero timestamps and normalize ownership for reproducibility
    ti.mtime = 0
    ti.uname = ''
    ti.gname = ''
    ti.uid = 0
    ti.gid = 0
    return ti


def create_tar_from_dir(directory: str) -> bytes:
    """Create a deterministic (reproducible) tar of `directory` and return bytes.

    - Entries are added in sorted order
    - File metadata (mtime, uid/gid, uname/gname) are normalized
    - No compression
    """
    buf = io.BytesIO()
    # use PAX format for consistent behavior
    with tarfile.open(fileobj=buf, mode='w', format=tarfile.PAX_FORMAT) as tar:
        # collect all files and dirs
        entries: List[str] = []
        for root, dirs, files in os.walk(directory):
            for d in dirs:
                full = os.path.join(root, d)
                entries.append(full)
            for f in files:
                full = os.path.join(root, f)
                entries.append(full)
        # sort by archive name (relative path)
        entries.sort(key=lambda p: os.path.relpath(p, start=directory))
        for full in entries:
            arcname = os.path.relpath(full, start=directory)
            if os.path.islink(full):
                # handle symlinks reproducibly
                ti = tar.gettarinfo(full, arcname=arcname)
                ti = _normalize_tarinfo(ti)
                ti.type = tarfile.SYMTYPE
                ti.linkname = os.readlink(full)
                tar.addfile(ti)
            elif os.path.isdir(full):
                ti = tar.gettarinfo(full, arcname=arcname)
                ti = _normalize_tarinfo(ti)
                tar.addfile(ti)
            else:
                with open(full, 'rb') as fobj:
                    data = fobj.read()
                ti = tarfile.TarInfo(name=arcname)
                ti.size = len(data)
                # set default mode; preserve executable bit if present
                st = os.stat(full)
                ti.mode = st.st_mode & 0o777
                ti = _normalize_tarinfo(ti)
                tar.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def extract_tar_bytes_to_dir(tar_bytes: bytes, dest: str):
    buf = io.BytesIO(tar_bytes)
    with tarfile.open(fileobj=buf, mode='r') as tar:
        tar.extractall(path=dest)


def write_tar_bytes_to_file(tar_bytes: bytes, path: str):
    with open(path, 'wb') as f:
        f.write(tar_bytes)


def read_tar_file(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()
