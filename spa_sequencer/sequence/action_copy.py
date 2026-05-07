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

    anim = new_obj.animation_data
    if anim is None:
        return new_obj

    if anim.action:
        anim.action = anim.action.copy()

    for track in anim.nla_tracks:
        for strip in track.strips:
            if strip.action:
                strip.action = strip.action.copy()

    return new_obj


# Manifest Helpers
def _col_has_manifest_objects(
    col: bpy.types.Collection,
    manifest: ActionManifest,
) -> bool:
    for obj in col.objects:
        if obj in manifest:
            return True
    for child in col.children:
        if _col_has_manifest_objects(child, manifest):
            return True
    return False


def _copy_collection_from_manifest(
    col: bpy.types.Collection,
    manifest: ActionManifest,
) -> bpy.types.Collection:
    """Create a collection if any children are animated or contain animated objs.
    Static objects and unaffected child collections remain as original links.
    Doesn't handle linking the result to a scene or parent collection.
    """
    new_col = bpy.data.collections.new(col.name)

    for obj in col.objects:
        new_col.objects.link(manifest.get(obj, obj))

    for child in col.children:
        if _col_has_manifest_objects(child, manifest):
            new_col.children.link(_copy_collection_from_manifest(child, manifest))
        else:
            new_col.children.link(child)

    return new_col


def _apply_manifest_to_scene(
    scene: bpy.types.Scene,
    manifest: ActionManifest,
) -> None:
    """Replace collections objects in scene."""
    for col in list(scene.collection.children):
        if _col_has_manifest_objects(col, manifest):
            new_col = _copy_collection_from_manifest(col, manifest)
            scene.collection.children.unlink(col)
            scene.collection.children.link(new_col)

    for obj in list(scene.collection.objects):
        if obj in manifest:
            scene.collection.objects.unlink(obj)
            scene.collection.objects.link(manifest[obj])


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
        bpy.ops.scene.new(type='LINK_COPY')

    new_scene: bpy.types.Scene = context.scene
    new_scene.name = name

    manifest: ActionManifest = {}

    def _collect(col: bpy.types.Collection) -> None:
        for obj in col.objects:
            if obj_has_animation(obj) and obj not in manifest:
                manifest[obj] = action_copy_object(obj)
        for child in col.children:
            _collect(child)

    _collect(ref_scene.collection)

    _apply_manifest_to_scene(new_scene, manifest)

    new_scene.camera = manifest.get(ref_scene.camera, ref_scene.camera)

    sync_system_update(context, force=True)
    return new_scene


# Object Copy in Scene
def action_copy_object_in_scene(
    context: bpy.types.Context,
    scene: bpy.types.Scene,
    objs: list[bpy.types.Object],
) -> list[bpy.types.Object]:
    #  TODOO  docstring
    manifest: ActionManifest = {obj: action_copy_object(obj) for obj in objs}

    _apply_manifest_to_scene(scene, manifest)

    sync_system_update(context, force=True)
    return list(manifest.values())
