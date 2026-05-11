# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from ..utils import register_classes, unregister_classes
from .core import (
    action_copy_object_in_scene,
)

class SEQUENCE_OT_action_copy_object(bpy.types.Operator):
    bl_idname = "sequence.action_copy_object"
    bl_label = "Action Copy Object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if not context.selected_objects:
            cls.poll_message_set("No selected objects")
            return False
        return True

    def execute(self, context: bpy.types.Context):
        objs = context.selected_objects
        scene = context.scene

        try:
            ac_manifest = action_copy_object_in_scene(context, scene, objs)
        except ValueError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Action copied {len(ac_manifest)} object(s)")
        return {"FINISHED"}


classes = (
    SEQUENCE_OT_action_copy_object,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
