# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from ..sync.core import get_sync_settings
from ..utils import register_classes, unregister_classes


class SEQUENCER_PT_SyncPanel(bpy.types.Panel):
    """Timeline Synchronization Panel."""

    bl_label = "Timeline Synchronization"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "SPA.Sequencer"
    bl_order = 1

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        settings = get_sync_settings()
        self.layout.operator(
            "wm.timeline_sync_toggle",
            text="Synchronize",
            icon="UV_SYNC_SELECT",
            depress=settings.enabled,
        )
        self.layout.prop(settings, "master_scene")


class SEQUENCER_PT_SyncPanelAdvancedSettings(bpy.types.Panel):
    """Timeline Synchronization advanced settings Panel."""

    bl_label = "Advanced Settings"
    bl_parent_id = "SEQUENCER_PT_SyncPanel"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "SPA.Sequencer"
    bl_order = 2

    def draw(self, context):
        settings = get_sync_settings()
        self.layout.prop(settings, "keep_gpencil_tool_settings")
        self.layout.prop(settings, "bidirectional")
        self.layout.prop(settings, "use_preview_range")
        self.layout.prop(settings, "sync_all_windows")
        self.layout.prop(settings, "active_follows_playhead")


class SEQUENCER_PT_scene_properties(bpy.types.Panel):
    """Adjust the scene properties of the active Sync Scene."""

    bl_label = "Scene Properties"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "SPA.Sequencer"
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene: bpy.types.Scene = get_sync_settings().master_scene

        if not scene:
            layout.label(text="Master Scene not Set", icon="SCENE_DATA")

        rd = scene.render

        layout.label(text=scene.name, icon="SCENE_DATA")
        layout.separator()

        col = layout.column(align=True)
        col.prop(rd, "resolution_x", text="Resolution X")
        col.prop(rd, "resolution_y", text="Y")
        col.prop(rd, "resolution_percentage", text="%")

        layout.separator()

        col = layout.column(heading="Frame Rate")
        bpy.types.RENDER_PT_format.draw_framerate(col, rd)

        layout.separator()

        col = layout.column(align=True)
        col.prop(scene, "frame_start", text="Frame Start")
        col.prop(scene, "frame_end", text="End")
        col.prop(scene, "frame_step", text="Step")


classes = (
    SEQUENCER_PT_SyncPanel,
    SEQUENCER_PT_SyncPanelAdvancedSettings,
    SEQUENCER_PT_scene_properties,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
