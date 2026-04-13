# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Pytest runner executed inside Blender.

Usage::

    local/blender/blender -b --factory-startup -P scripts/run_pytest.py -- [pytest_args]

Sets up the addon source directory as a local extension repository,
refreshes extensions so Blender discovers the addon, then runs pytest.
All arguments after ``--`` are forwarded to ``pytest.main()``.
"""

import sys
from pathlib import Path

import bpy
import addon_utils

try:
    import pytest
except ImportError:
    print(
        "ERROR: pytest is not installed in Blender's Python.\n"
        "Install it into Blender's bundled Python, e.g.:\n"
        "  local/blender/5.1/python/bin/python3.11 -m pip install pytest",
        file=sys.stderr,
    )
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_FOLDER = str(REPO_ROOT / "tests")
ADDON_DIR = str(REPO_ROOT)
REPO_MODULE = "spark_dev"


def setup_extension():
    """Register the addon source as a local extension repository."""
    repos = bpy.context.preferences.extensions.repos
    repo = repos.new(
        name="SPArk Dev",
        module=REPO_MODULE,
        custom_directory=ADDON_DIR,
    )
    repo.use_custom_directory = True
    addon_utils.extensions_refresh(ensure_wheels=True)


def main(args):
    """Set up extension environment, then run tests."""
    setup_extension()
    return pytest.main([TESTS_FOLDER] + args)


if __name__ == "__main__":
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    sys.exit(main(script_args))
