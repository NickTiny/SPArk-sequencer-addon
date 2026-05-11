# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy


def draw_outliner_context_menu(self, context):
    """Append action copy to Outliner context menu."""
    self.layout.operator(
            "sequence.action_copy_object",
            text="Action Copy Selected Objects",
            icon="DUPLICATE",
        )


def register():
    bpy.types.OUTLINER_MT_object.append(draw_outliner_context_menu)


def unregister():
    bpy.types.OUTLINER_MT_object.remove(draw_outliner_context_menu)
