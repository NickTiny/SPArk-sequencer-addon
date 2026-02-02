# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
import tempfile
import os

from pytest import fixture

from utils import create_shot_scene
from spa_sequencer.render.props import BLENDER_EEVEE


@fixture
def basic_render_setup() -> tuple[bpy.types.Scene, bpy.types.SceneStrip]:
    """
    Generate a basic setup with an edit scene and 1 shot scene ready for rendering.
    Returns the edit scene and the shot strip.
    """
    # Use default scene as edit scene and create the sequence editor
    edit_scene = bpy.context.scene
    edit_scene.name = "EDIT"
    edit_scene.sequence_editor_create()

    shot_strip = create_shot_scene(edit_scene, 1, 1)
    shot_scene = shot_strip.scene

    # Add basic render objects to the shot scene
    bpy.context.window.scene = shot_scene
    if not shot_scene.objects:
        bpy.ops.mesh.primitive_cube_add()
    if not shot_scene.camera:
        bpy.ops.object.camera_add()
        shot_scene.camera = bpy.context.active_object

    # Set shot strip duration to just 1 frame for fast testing
    shot_strip.frame_final_duration = 1

    # Switch back to edit scene
    bpy.context.window.scene = edit_scene

    return edit_scene, shot_strip


def _render_with_engine(basic_render_setup, engine_name, media_type="IMAGES"):
    """Helper function to test rendering with a specific engine."""
    edit_scene, shot_strip = basic_render_setup
    
    # Set up render options
    render_options = edit_scene.batch_render_options
    render_options.render_engine = engine_name
    render_options.media_type = media_type
    render_options.resolution = "25"  # 1/4 resolution for speed
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        render_options.filepath_pattern = os.path.join(temp_dir, "{strip}")
        
        # Select the shot strip for rendering
        edit_scene.sequence_editor.active_strip = shot_strip
        shot_strip.select = True
        render_options.selection_only = True
        
        result = bpy.ops.sequencer.batch_render()
        assert result == {"FINISHED"}


def test_workbench_render_images(basic_render_setup):
    """Test rendering with Workbench engine."""
    _render_with_engine(basic_render_setup, "BLENDER_WORKBENCH")
    
def test_eevee_render_images(basic_render_setup):
    """Test rendering with Eevee engine."""
    _render_with_engine(basic_render_setup, BLENDER_EEVEE)
    
def test_cycles_render_images(basic_render_setup):
    """Test rendering with Cycles engine."""
    _render_with_engine(basic_render_setup, "CYCLES")

def test_movie_after_images(basic_render_setup):
    """Test rendering with Workbench engine."""
    _render_with_engine(basic_render_setup, "BLENDER_WORKBENCH", media_type="MOVIE")
    
def test_images_after_movie(basic_render_setup):
    """Test rendering with Workbench engine."""
    _render_with_engine(basic_render_setup, "BLENDER_WORKBENCH", media_type="IMAGES")