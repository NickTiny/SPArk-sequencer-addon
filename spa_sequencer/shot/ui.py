# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from ..utils import register_classes, unregister_classes
from .ops import SEQUENCER_OT_new_shot_audition, SEQUENCER_OT_set_shot_audition, SEQUENCER_OT_shot_audition_set_menu
from .core import get_audition_strip
class SEQUENCER_MT_shot_clean_up(bpy.types.Menu):
    """Shot clean-up menu"""

    bl_idname = "SEQUENCER_MT_shot_clean_up"
    bl_label = "Clean Up"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.shot_chronological_numbering")


class SEQUENCER_MT_shot(bpy.types.Menu):
    """Shot operators menu"""

    bl_idname = "SEQUENCER_MT_shot"
    bl_label = "Shot"

    def draw(self, context):
        layout = self.layout

        layout.operator("sequencer.shot_new", text="New...")
        layout.operator("sequencer.shot_duplicate")
        layout.operator("sequencer.shot_delete", text="Delete...")
        layout.separator()
        layout.menu("SEQUENCER_MT_shot_audition")
        layout.separator()
        layout.operator("sequencer.shot_rename", text="Rename...")
        layout.operator("sequencer.shot_timing_adjust")
        layout.separator()
        layout.menu("SEQUENCER_MT_shot_clean_up")


def draw_MT_shot(self, context):
    layout = self.layout
    layout.menu(SEQUENCER_MT_shot.bl_idname)



class SEQUENCER_MT_shot_audition_set(bpy.types.Menu):
    """Shot audition set menu"""

    bl_idname = "SEQUENCER_MT_shot_audition_set"
    bl_label = "Audition Set Active"

    def draw(self, context):
        layout = self.layout
        audition_strip = get_audition_strip(context.active_strip)
        if not audition_strip:
            layout.label(text="No Active Audition Group")
            return
        for strip in sorted(audition_strip.strips, key=lambda s: s.name):
            row = layout.row()
            row.operator_context = "EXEC_DEFAULT"
            row.operator(SEQUENCER_OT_set_shot_audition.bl_idname, text=strip.name).audition_strip_selector = strip.name
            row.active = audition_strip.audition.active != strip.name
class SEQUENCER_MT_shot_audition(bpy.types.Menu):
    """Shot audition operators menu"""

    bl_idname = "SEQUENCER_MT_shot_audition"
    bl_label = "Audition"

    def draw(self, context):
        layout = self.layout
        layout.operator(SEQUENCER_OT_new_shot_audition.bl_idname, text="Make Group")
        layout.operator(SEQUENCER_OT_shot_audition_set_menu.bl_idname, text="Set Active")
        layout.operator("sequencer.meta_separate", text="Ungroup")


classes = (
    SEQUENCER_MT_shot,
    SEQUENCER_MT_shot_clean_up,
    SEQUENCER_MT_shot_audition,
    SEQUENCER_MT_shot_audition_set,
)


def register():
    register_classes(classes)

    # Add SEQUENCER_MT_shot to the sequencer editor menus
    bpy.types.SEQUENCER_MT_editor_menus.append(draw_MT_shot)


def unregister():
    unregister_classes(classes)

    # Remove SEQUENCER_MT_shot from the sequencer editor menus
    bpy.types.SEQUENCER_MT_editor_menus.remove(draw_MT_shot)
