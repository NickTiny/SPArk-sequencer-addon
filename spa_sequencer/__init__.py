# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from . import (
    editorial,
    keymaps,
    preferences,
    render,
    sequence,
    shared_folders,
    shot,
    sync,
)


packages = (
    sync,
    shot,
    sequence,
    render,
    editorial,
    shared_folders,
    preferences,
    keymaps,
)


def register():
    for package in packages:
        package.register()


def unregister():
    for package in packages:
        package.unregister()
