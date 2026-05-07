# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
import pytest

from utils import import_spa_sequencer_module

import_spa_sequencer_module()

from spa_sequencer.sequence.action_copy import (
    _action_copy_object,
    action_copy_object_in_scene,
    action_copy_scene,
)

# LLM Generated Testes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_animated_object(name: str) -> bpy.types.Object:
    """Create an object with a keyframed location (has animation data)."""
    obj = bpy.data.objects.new(name, None)
    obj.location = (0, 0, 0)
    obj.keyframe_insert("location", frame=1)
    obj.keyframe_insert("location", frame=10)
    return obj


def _make_static_object(name: str) -> bpy.types.Object:
    """Create an object with no animation data."""
    return bpy.data.objects.new(name, None)


def _make_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.new(name)
    return col


# ---------------------------------------------------------------------------
# action_copy_object
# ---------------------------------------------------------------------------

class TestActionCopyObject:
    def test_no_animation_data(self):
        """Static object: linked duplicate, shared mesh data."""
        mesh = bpy.data.meshes.new("Mesh")
        obj = bpy.data.objects.new("Static", mesh)
        copy = _action_copy_object(obj)
        assert copy is not obj
        assert copy.data is obj.data

    def test_active_action_is_independent(self):
        """Active action on copy must be a different ID than the original."""
        obj = _make_animated_object("AnimObj")
        original_action = obj.animation_data.action
        copy = _action_copy_object(obj)
        assert copy.animation_data.action is not original_action

    def test_nla_strip_actions_are_independent(self):
        """All NLA strip actions on copy must be different IDs from originals."""
        obj = _make_animated_object("NLAObj")
        anim = obj.animation_data
        # Push action down to an NLA track and clear the active action.
        track = anim.nla_tracks.new()
        strip = track.strips.new("Strip", 1, anim.action)
        anim.action = None

        original_strip_action = strip.action
        copy = _action_copy_object(obj)
        copy_strip_action = copy.animation_data.nla_tracks[0].strips[0].action
        assert copy_strip_action is not original_strip_action


# ---------------------------------------------------------------------------
# action_copy_scene — tests over the whole-scene copy path
# ---------------------------------------------------------------------------

class TestActionCopyScene:
    def test_static_scene_no_new_collections(self):
        """Scene with no animated objects: collections are the same references."""
        scene = bpy.context.scene
        static_obj = _make_static_object("Static")
        col = _make_collection("StaticCol")
        col.objects.link(static_obj)
        scene.collection.children.link(col)

        collections_before = set(bpy.data.collections)
        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        # No new collections should have been created.
        new_collections = set(bpy.data.collections) - collections_before
        assert not new_collections
        # The original collection is still present in the new scene unchanged.
        assert col in new_scene.collection.children.values()

    def test_animated_collection_is_replaced(self):
        """Collection containing an animated object is replaced by a new one."""
        scene = bpy.context.scene
        anim_obj = _make_animated_object("AnimObj")
        col = _make_collection("AnimCol")
        col.objects.link(anim_obj)
        scene.collection.children.link(col)

        original_children = set(scene.collection.children.values())
        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        # Original collection is gone; exactly one new collection took its place.
        assert col not in new_scene.collection.children.values()
        new_children = set(new_scene.collection.children.values()) - original_children
        assert len(new_children) == 1

    def test_animated_object_in_collection_is_copied(self):
        """Animated object inside a collection gets an independent action copy."""
        scene = bpy.context.scene
        anim_obj = _make_animated_object("AnimObj")
        original_action = anim_obj.animation_data.action
        col = _make_collection("AnimCol")
        col.objects.link(anim_obj)
        scene.collection.children.link(col)

        original_children = set(scene.collection.children.values())
        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        # Find the replacement collection by set difference (name may be auto-incremented).
        new_col = next(c for c in new_scene.collection.children.values() if c not in original_children)
        new_obj = list(new_col.objects)[0]
        assert new_obj is not anim_obj
        assert new_obj.animation_data.action is not original_action

    def test_static_sibling_collection_kept(self):
        """Static sibling collection is not replaced (same reference)."""
        scene = bpy.context.scene
        anim_obj = _make_animated_object("AnimObj")
        static_obj = _make_static_object("StaticObj")

        anim_col = _make_collection("AnimCol")
        anim_col.objects.link(anim_obj)
        static_col = _make_collection("StaticCol")
        static_col.objects.link(static_obj)

        scene.collection.children.link(anim_col)
        scene.collection.children.link(static_col)

        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        assert static_col in new_scene.collection.children.values()

    def test_animated_object_in_nested_collection(self):
        """Animated object in a deeply nested collection: all ancestors replaced."""
        scene = bpy.context.scene
        anim_obj = _make_animated_object("Deep")
        inner = _make_collection("Inner")
        inner.objects.link(anim_obj)
        outer = _make_collection("Outer")
        outer.children.link(inner)
        scene.collection.children.link(outer)

        original_children = set(scene.collection.children.values())
        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        # Outer replaced: find by set difference.
        assert outer not in new_scene.collection.children.values()
        new_outer = next(c for c in new_scene.collection.children.values() if c not in original_children)
        # Inner also replaced.
        assert inner not in new_outer.children.values()
        new_inner = next(c for c in new_outer.children.values() if c is not inner)
        # A copied object (not the original) lives in the new inner collection.
        new_obj = list(new_inner.objects)[0]
        assert new_obj is not anim_obj

    def test_animated_camera_remapped(self):
        """If the scene camera is animated, new_scene.camera is the copy."""
        scene = bpy.context.scene
        cam_data = bpy.data.cameras.new("Cam")
        cam_obj = bpy.data.objects.new("Camera", cam_data)
        cam_obj.keyframe_insert("location", frame=1)
        col = _make_collection("CamCol")
        col.objects.link(cam_obj)
        scene.collection.children.link(col)
        scene.camera = cam_obj

        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        # Camera is animated: new scene must point at the copy, not the original.
        assert new_scene.camera is not cam_obj
        assert new_scene.camera.data is cam_obj.data

    def test_static_camera_preserved(self):
        """If the scene camera is static, new_scene.camera is the original."""
        scene = bpy.context.scene
        cam_data = bpy.data.cameras.new("Cam")
        cam_obj = bpy.data.objects.new("Camera", cam_data)
        col = _make_collection("CamCol")
        col.objects.link(cam_obj)
        scene.collection.children.link(col)
        scene.camera = cam_obj

        new_scene = action_copy_scene(bpy.context, scene, "CopyScene")

        assert new_scene.camera is cam_obj


# ---------------------------------------------------------------------------
# action_copy_object_in_scene — tests over the selective-object copy path
# ---------------------------------------------------------------------------

class TestActionCopyObjectInScene:
    def test_object_in_scene_collection(self):
        """Object directly in scene.collection is replaced."""
        scene = bpy.context.scene
        obj = _make_animated_object("Direct")
        scene.collection.objects.link(obj)

        new_objs = action_copy_object_in_scene(bpy.context, scene, [obj])

        assert obj not in scene.collection.objects.values()
        assert new_objs[0] in scene.collection.objects.values()

    def test_object_in_nested_collection_ancestors_replaced(self):
        """Ancestor collections up to the scene root are all replaced."""
        scene = bpy.context.scene
        obj = _make_animated_object("Nested")
        inner = _make_collection("Inner")
        inner.objects.link(obj)
        outer = _make_collection("Outer")
        outer.children.link(inner)
        scene.collection.children.link(outer)

        original_children = set(scene.collection.children.values())
        action_copy_object_in_scene(bpy.context, scene, [obj])

        assert outer not in scene.collection.children.values()
        new_outer = next(c for c in scene.collection.children.values() if c not in original_children)
        assert inner not in new_outer.children.values()

    def test_two_objects_same_collection_one_new_collection(self):
        """Two objects in the same collection → exactly ONE new collection, not two."""
        scene = bpy.context.scene
        obj_a = _make_animated_object("ObjA")
        obj_b = _make_animated_object("ObjB")
        col = _make_collection("SharedCol")
        col.objects.link(obj_a)
        col.objects.link(obj_b)
        scene.collection.children.link(col)

        collections_before = set(bpy.data.collections)
        new_objs = action_copy_object_in_scene(bpy.context, scene, [obj_a, obj_b])
        new_collections = set(bpy.data.collections) - collections_before

        # Only the one shared collection should have been duplicated.
        assert len(new_collections) == 1
        assert len(new_objs) == 2

    def test_static_sibling_collection_unchanged(self):
        """Static sibling collection is not replaced."""
        scene = bpy.context.scene
        anim_obj = _make_animated_object("Anim")
        static_obj = _make_static_object("Static")

        anim_col = _make_collection("AnimCol")
        anim_col.objects.link(anim_obj)
        static_col = _make_collection("StaticCol")
        static_col.objects.link(static_obj)

        scene.collection.children.link(anim_col)
        scene.collection.children.link(static_col)

        action_copy_object_in_scene(bpy.context, scene, [anim_obj])

        assert static_col in scene.collection.children.values()

    def test_object_linked_in_multiple_collections_all_instances_replaced(self):
        """Object in two collections → both instances replaced by the same new object."""
        scene = bpy.context.scene
        obj = _make_animated_object("Multi")
        col_a = _make_collection("ColA")
        col_b = _make_collection("ColB")
        col_a.objects.link(obj)
        col_b.objects.link(obj)
        scene.collection.children.link(col_a)
        scene.collection.children.link(col_b)

        original_children = set(scene.collection.children.values())
        new_objs = action_copy_object_in_scene(bpy.context, scene, [obj])
        new_obj = new_objs[0]

        # Both original collections are replaced; find the two new ones by set difference.
        new_children = set(scene.collection.children.values()) - original_children
        assert len(new_children) == 2
        for new_child in new_children:
            assert new_obj in new_child.objects.values()
            assert obj not in new_child.objects.values()

    def test_copied_object_has_independent_action(self):
        scene = bpy.context.scene
        obj = _make_animated_object("Anim")
        original_action = obj.animation_data.action
        col = _make_collection("Col")
        col.objects.link(obj)
        scene.collection.children.link(col)

        new_objs = action_copy_object_in_scene(bpy.context, scene, [obj])

        assert new_objs[0].animation_data.action is not original_action
