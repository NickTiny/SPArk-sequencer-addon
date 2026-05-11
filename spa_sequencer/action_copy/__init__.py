# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from . import (
    ops,
)


def register():
    ops.register()


def unregister():
    ops.unregister()
