# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Addon preferences management.
"""

import bpy

from .utils import register_classes, unregister_classes


def update_jump_strip_keymap(self, context):
    """Toggle jump strip keymaps when preference changes."""
    from .keymaps import addon_keymaps
    
    # Toggle active state on existing keymap items
    for km, kmi in addon_keymaps:
        if kmi.idname == "sequence.strip_jump_anywhere":
            kmi.active = self.enable_jump_strip_keymap


class SPASequencerAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shot_template_prefix: bpy.props.StringProperty(
        name="Shot Template Prefix",
        description="Scene name prefix that identifies Shot Templates",
        default="TEMPLATE_SHOT",
    )
    
    enable_jump_strip_keymap: bpy.props.BoolProperty(
        name="Enable Jump Strip Keymaps",
        description=(
            "Enable PageUp/PageDown keymaps for jumping between strips from anywhere. "
            "When enabled, PageUp/PageDown will jump to previous/next strip in the master timeline"
        ),
        default=False,
        update=update_jump_strip_keymap,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shot_template_prefix")
        
        box = layout.box()
        box.label(text="Keymaps:", icon="KEYINGSET")
        box.prop(self, "enable_jump_strip_keymap")


def get_addon_prefs() -> SPASequencerAddonPreferences:
    """Get the Addon Preferences instance."""
    return bpy.context.preferences.addons[__package__].preferences


classes = (SPASequencerAddonPreferences,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
