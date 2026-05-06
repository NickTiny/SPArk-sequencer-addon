# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.
import bpy

from ..sync.core import sync_system_update

# Maps original Object -> action-copied Object, used for camera remapping.
ActionManifest = dict[bpy.types.Object, bpy.types.Object]

# Core Helpers
def obj_has_animation(obj: bpy.types.Object) -> bool:
    """Return True if *obj* carries an action or any NLA tracks."""
    anim = obj.animation_data
    if not anim:
        return False
    if anim.action:
        return True
    if anim.nla_tracks:
        return True
    return False


def col_has_animated_objects(col: bpy.types.Collection) -> bool:
    """Return True if *col* or any descendant collection contains an animated object."""
    for obj in col.objects:
        if obj_has_animation(obj):
            return True
    for child in col.children:
        if col_has_animated_objects(child):
            return True
    return False

# Object Level
def action_copy_object(obj: bpy.types.Object) -> bpy.types.Object:
    """Create a linked duplicate of *obj* with independent animation data.
    Doesn't handle linking object to scene or collection.
    """

    new_obj = obj.copy()
    # obj.copy() keeps new_obj.data pointing at the same mesh ID → shared ✓

    anim = new_obj.animation_data
    if anim is None:
        return new_obj

    # Detach the active action so it is independent.
    if anim.action:
        anim.action = anim.action.copy()

    # Detach actions referenced by every NLA strip.
    for track in anim.nla_tracks:
        for strip in track.strips:
            if strip.action:
                strip.action = strip.action.copy()

    return new_obj


# Collection Level
def action_copy_collection(
    col: bpy.types.Collection,
    manifest: ActionManifest,
) -> bpy.types.Collection:
    """Build a new collection that mirrors input but has action copy objects.

    Static objects and child collections remain as original links. Animated
    objects are duplicated (and all the ancestor collections).

    Doesn't handle linking collection to scene.
    """
    new_col = bpy.data.collections.new(col.name)

    for obj in col.objects:
        if obj_has_animation(obj):
            new_obj = action_copy_object(obj)
            manifest[obj] = new_obj
            new_col.objects.link(new_obj)
        else:
            new_col.objects.link(obj)

    for child in col.children:
        if col_has_animated_objects(child):
            new_child = action_copy_collection(child, manifest)
            new_col.children.link(new_child)
        else:
            new_col.children.link(child)

    return new_col


# Scene Level
def action_copy_scene(
    context: bpy.types.Context,
    ref_scene: bpy.types.Scene,
    name: str,
) -> bpy.types.Scene:
    """Create a new scene that is an action copy of the input scene.

    Static objects and child collections remain as original links. Animated
    objects are duplicated (and all the ancestor collections). Objects linked
    to scene collection are also checked.
    """
    with context.temp_override(scene=ref_scene):
        bpy.ops.scene.new('LINK_COPY')

    new_scene: bpy.types.Scene = context.scene
    new_scene.name = name

    manifest: ActionManifest = {}

    for col in ref_scene.collection.children:
        if col_has_animated_objects(col):
            # Populate object manifest
            new_col = action_copy_collection(col, manifest)

            # Replace collections
            new_scene.collection.children.link(new_col)
            new_scene.collection.children.unlink(col)

    for obj in ref_scene.collection.objects:
        if obj_has_animation(obj):
            new_obj = action_copy_object(obj)
            # TODO perhaps manifest isn't needed if it's only used for camera?
            manifest[obj] = new_obj  # Populate manifest incase scene camera is here
            new_scene.collection.objects.link(new_obj)
            new_scene.collection.objects.unlink(new_obj)

    new_scene.camera = manifest.get(ref_scene.camera, ref_scene.camera)

    sync_system_update(context, force=True)
    return new_scene


# Object Copy Operator Helpers
def _find_object_collection_paths(
    scene: bpy.types.Scene,
    obj: bpy.types.Object,
) -> list[list[bpy.types.Collection]]:
    """Return one path [scene.collection, …, parent] for every collection that
    directly contains *obj*, found in a single tree traversal."""
    paths: list[list[bpy.types.Collection]] = []

    def _walk(col: bpy.types.Collection, current: list[bpy.types.Collection]) -> None:
        path = current + [col]
        if obj.name in col.objects:
            paths.append(path)
        for child in col.children:
            _walk(child, path)

    _walk(scene.collection, [])
    return paths


def _shallow_duplicate_collection(
    col: bpy.types.Collection,
    old_obj: bpy.types.Object,
    new_obj: bpy.types.Object,
) -> bpy.types.Collection:
    """Replace collection with action collection"""
    # TODO Not sure if we need this maybe just used the main collection copy... hmmm
    new_col = bpy.data.collections.new(col.name)
    for o in col.objects:
        new_col.objects.link(new_obj if o == old_obj else o)
    for child in col.children:
        new_col.children.link(child)
    return new_col


# NOTE: This is a bit confused now it's all laid out.
# I think that this function because it more gracefully handles
# Multiple objects should be out main engine. TBD consoildation.
# TODO Need a list test senarios to verify the logic here...
def action_copy_object_in_scene(
    context: bpy.types.Context,
    scene: bpy.types.Scene,
    objs: list[bpy.types.Object],
) -> list[bpy.types.Object]:
    # TODO docstring
    # Implementation for object action copy operator
    # Commenting out for now....
    new_objs: list[bpy.types.Object] = []

    for obj in objs:
        paths = _find_object_collection_paths(scene, obj)
        if not paths:
            raise ValueError(f"Object '{obj.name}' is not in scene '{scene.name}'")

        new_obj = action_copy_object(obj)
        new_objs.append(new_obj)

        for path in paths:
            parent_col = path[-1]  # TODO maybe should be manifest?

            # If object in scene collection fix here and don't loop over ancestors
            if parent_col is scene.collection:
                scene.collection.objects.unlink(obj)
                scene.collection.objects.link(new_obj)
                continue

            # Object in a collection. Replace immediate parent
            current_old = parent_col
            current_new = _shallow_duplicate_collection(parent_col, obj, new_obj)

            # Replace all ancestors
            for ancestor in reversed(path[1:-1]):
                new_ancestor = bpy.data.collections.new(ancestor.name)
                for o in ancestor.objects:
                    new_ancestor.objects.link(o)
                for c in ancestor.children:
                    new_ancestor.children.link(current_new if c is current_old else c)
                current_old = ancestor
                current_new = new_ancestor

            # Set ancestors in the scene collection (replaced parents all the way up)
            scene.collection.children.unlink(path[1])
            scene.collection.children.link(current_new)

    sync_system_update(context, force=True)
    return new_objs
