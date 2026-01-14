# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
import importlib
import addon_utils
import sys

def create_shot_scene(
    edit_scene: bpy.types.Scene, channel: int, frame_start: int
) -> bpy.types.SceneStrip:
    """
    Create a new empty scene and adds it as a strip in `edit_scene`'s sequence editor.

    :param edit_scene: The edit scene
    :param channel: Shot strip's channel
    :param frame_start: Shot strip's frame start
    :return: The created shot strip
    """
    # Create a new scene
    shot_scene = bpy.data.scenes.new(name="SHOT")
    # Add a scene strip in the edit scene's sequence editor
    shot_strip = edit_scene.sequence_editor.strips.new_scene(
        name=shot_scene.name,
        scene=shot_scene,
        channel=channel,
        frame_start=frame_start,
    )
    return shot_strip


def get_module_name():
    for module in addon_utils.modules():
        if module.__name__.endswith("spa_sequencer"):
            return module.__name__

def import_spa_sequencer_module():
    spa_sequencer = importlib.import_module(get_module_name())
    sys.modules["spa_sequencer"] = spa_sequencer