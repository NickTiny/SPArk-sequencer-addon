#!/usr/bin/env python3
"""
Download binary wheels for platforms listed from requirements.txt.

Default behavior:
 - Reads requirements from repo root requirements.txt
 - Places wheels in spa_sequencer/wheels
 - Downloads for platforms: macosx_11_0_arm64, win_amd64, manylinux2014_x86_64
 - Uses Python version tag 3.11 by default

Usage:
  python fetch_wheels.py
  python fetch_wheels.py --per-package   # download per requirement line
  python fetch_wheels.py -r path/to/reqs -o out/dir -P manylinux2014_x86_64
"""
from pathlib import Path
import argparse
import subprocess
import sys
from typing import List, Tuple

DEFAULT_PLATFORMS = [
    "macosx_11_0_arm64",
    "win_amd64",
    "manylinux2014_x86_64",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download wheels for platforms from requirements.txt")
    p.add_argument("--requirements", "-r", type=Path, default=Path("requirements.txt"),
                   help="Path to requirements.txt")
    p.add_argument("--output", "-o", type=Path, default=Path("spa_sequencer") / "wheels",
                   help="Directory to place downloaded wheels")
    p.add_argument("--python-version", "-p", default="3.11",
                   help="Python version tag to pass to pip (e.g., 3.11)")
    p.add_argument("--platforms", "-P", nargs="+", default=DEFAULT_PLATFORMS,
                   help="Platform tags to download for")
    p.add_argument("--per-package", action="store_true",
                   help="Download per requirement line (skipping -/comments) instead of using -r requirements.txt")
    return p.parse_args()


def parse_requirements(requirements_file: Path) -> List[str]:
    if not requirements_file.exists():
        raise FileNotFoundError(f"{requirements_file} does not exist")
    reqs: List[str] = []
    with open(requirements_file, "r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("-"):
                continue
            reqs.append(s)
    return reqs


def run_pip_download(cmd: List[str]) -> bool:
    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        return False


def download_per_package(requirements: List[str], platforms: List[str], out_dir: Path, python_version: str) -> List[Tuple[str, str]]:
    failed: List[Tuple[str, str]] = []
    for req in requirements:
        for platform in platforms:
            cmd = [
                sys.executable, "-m", "pip", "download", req,
                "--dest", str(out_dir),
                "--only-binary=:all:",
                "--platform", platform,
                "--python-version", python_version,
            ]
            if not run_pip_download(cmd):
                failed.append((req, platform))
    return failed


def download_requirements_file(req_file: Path, platforms: List[str], out_dir: Path, python_version: str) -> List[Tuple[str, str]]:
    failed: List[Tuple[str, str]] = []
    for platform in platforms:
        cmd = [
            sys.executable, "-m", "pip", "download",
            "-r", str(req_file),
            "--dest", str(out_dir),
            "--only-binary=:all:",
            "--platform", platform,
            "--python-version", python_version,
        ]
        if not run_pip_download(cmd):
            failed.append((str(req_file), platform))
    return failed


def main() -> None:
    args = parse_args()
    req_file: Path = args.requirements
    out_dir: Path = args.output
    python_version: str = args.python_version
    platforms: List[str] = args.platforms

    if not req_file.exists():
        print(f"Requirements file not found: {req_file}")
        sys.exit(2)

    out_dir.mkdir(parents=True, exist_ok=True)

    failed: List[Tuple[str, str]] = []
    if args.per_package:
        requirements = parse_requirements(req_file)
        failed = download_per_package(requirements, platforms, out_dir, python_version)
    else:
        failed = download_requirements_file(req_file, platforms, out_dir, python_version)

    if failed:
        print("Some downloads failed:", failed)
        sys.exit(1)

    print("Done. Wheels placed in", out_dir)


if __name__ == "__main__":
    main()