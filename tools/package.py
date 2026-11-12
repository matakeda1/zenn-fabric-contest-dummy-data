"""Build the distributable ZIP files.

    python tools/package.py --dest <folder> [--version v0.1]

Creates <name>_<version>_full.zip (whole repo except .git) and <name>_<version>_participants.zip
(README, data/, docs/, tools/replay_sensor_to_eventstream.py) with a single top-level folder.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "zenn-fabric-contest-dummy-data"
SKIP_DIRS = {".git", "__pycache__", ".venv", "dist"}


def files_full():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            yield p


def files_participants():
    for p in files_full():
        rel = p.relative_to(ROOT)
        top = rel.parts[0]
        if top in ("data", "docs") or rel.as_posix() in ("README.md", "tools/replay_sensor_to_eventstream.py"):
            yield p


def build(dest: Path, version: str, kind: str, files):
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"{NAME}_{version}_{kind}.zip"
    n = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, f"{NAME}/{p.relative_to(ROOT).as_posix()}")
            n += 1
    print(f"{out}  files={n}  size={out.stat().st_size / 1e6:.1f} MB")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--version", default="v0.1")
    a = ap.parse_args()
    dest = Path(a.dest)
    build(dest, a.version, "participants", files_participants())
    build(dest, a.version, "full", files_full())


if __name__ == "__main__":
    main()
