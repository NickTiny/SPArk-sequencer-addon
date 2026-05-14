# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Addon preferences management.
"""

import bpy

from .utils import register_classes, unregister_classes


class SPASequencerAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    # Empty for now but may be useful for future features

def get_addon_prefs() -> SPASequencerAddonPreferences:
    """Get the Addon Preferences instance."""
    return bpy.context.preferences.addons[__package__].preferences


classes = (SPASequencerAddonPreferences,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
