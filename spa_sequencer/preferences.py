# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Addon preferences management.
"""

import bpy

from .utils import register_classes, unregister_classes


class SPASequencerAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shot_template_prefix: bpy.props.StringProperty(
        name="Shot Template Prefix",
        description="Scene name prefix that identifies Shot Templates",
        default="TEMPLATE_SHOT",
    )

    override_stamp_settings: bpy.props.BoolProperty(
        name="Use Custom Burn-Ins",
        description=(
            "Disabling this option allows the user to set custom burn-in settings "
            "under their scene settings on a per file basis. Otherwise the Sequencer "
            "will automatically burn in the Date, Frame, Camera, Lens, Scene, Filename "
            "Stripname and Artist's username to all Sequencer Batch Renders"
        ),
        default=True,
    )

    def draw(self, context):
        self.layout.prop(self, "shot_template_prefix")
        self.layout.prop(self, "override_stamp_settings")


def get_addon_prefs() -> SPASequencerAddonPreferences:
    """Get the Addon Preferences instance."""
    return bpy.context.preferences.addons[__package__].preferences


classes = (SPASequencerAddonPreferences,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
