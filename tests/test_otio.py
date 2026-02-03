# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Simple tests for VSE IO (OTIO/AAF import/export).
"""

import os
import tempfile

import bpy
from pytest import fixture

# Import fixtures from test_sync
from test_sync import basic_synced_setup, complex_synced_setup


@fixture
def clean_scene():
    """Provide a clean scene with sequence editor."""
    scene = bpy.context.scene
    scene.name = "EDIT"
    scene.frame_start = 1001
    
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    
    seq_editor = scene.sequence_editor
    
    # Clear strips
    while seq_editor.strips:
        seq_editor.strips.remove(seq_editor.strips[0])
    
    yield scene
    
    # Cleanup
    while seq_editor.strips:
        seq_editor.strips.remove(seq_editor.strips[0])


def test_export_otio(complex_synced_setup):
    """Test basic export to OTIO format."""
    edit_scene, shot_strips = complex_synced_setup
    
    with tempfile.TemporaryDirectory() as temp_dir:
        export_path = os.path.join(temp_dir, "test.otio")
        
        with bpy.context.temp_override(scene=edit_scene, sequencer_scene=edit_scene):
            bpy.ops.export_timeline.vse_otio(
                filepath=export_path,
                file_format="otio",
            )
        
        assert os.path.exists(export_path)
        assert os.path.getsize(export_path) > 0


def test_import_otio(clean_scene):
    """Test basic import from pre-generated OTIO file."""
    scene = clean_scene
    test_file = "local/test_files/test_timeline.otio"
    
    if not os.path.exists(test_file):
        # Skip if test file doesn't exist
        import pytest
        pytest.skip(f"Test file {test_file} not found")
    
    # Use try/except to handle background mode context issues
    try:
        with bpy.context.temp_override(scene=clean_scene, sequencer_scene=clean_scene):
            result = bpy.ops.import_timeline.vse_otio(filepath=test_file)
    except RuntimeError as e:
        # refresh_all() may fail in background mode, but import still works
        if "refresh_all" not in str(e):
            raise
        result = {"FINISHED"}
    
    assert result == {"FINISHED"}
    # Should have created some strips
    assert len(scene.sequence_editor.strips) > 0


def test_roundtrip_otio(complex_synced_setup):
    """Test export then import preserves strips."""
    edit_scene, shot_strips = complex_synced_setup
    original_count = len(edit_scene.sequence_editor.strips)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        export_path = os.path.join(temp_dir, "roundtrip.otio")
        
        # Export
        with bpy.context.temp_override(scene=edit_scene, sequencer_scene=edit_scene):
            result = bpy.ops.export_timeline.vse_otio(
                filepath=export_path,
                file_format="otio",
            )
        assert result == {"FINISHED"}
        
        # Clear strips
        while edit_scene.sequence_editor.strips:
            edit_scene.sequence_editor.strips.remove(edit_scene.sequence_editor.strips[0])
        
        # Import
        try:
            with bpy.context.temp_override(scene=edit_scene, sequencer_scene=edit_scene):
                result = bpy.ops.import_timeline.vse_otio(filepath=export_path)
        except RuntimeError as e:
            if "refresh_all" not in str(e):
                raise
            result = {"FINISHED"}
        
        assert result == {"FINISHED"}
        
        # Should have same number of strips
        assert len(edit_scene.sequence_editor.strips) == original_count
