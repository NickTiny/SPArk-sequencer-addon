# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.
import bpy
from bpy.types import Object, Collection, Scene, Context

from ..sync.core import sync_system_update


# Helpers
def _obj_has_animation(obj: Object) -> bool:
    """Return True if object is animated"""

    anim = obj.animation_data
    return bool(anim and (anim.action or anim.nla_tracks))


def _action_copy_object(obj: Object) -> Object:
    """Create a linked duplicate of an object"""
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


# Core Logic
def _apply_action_copy(scene: Scene, objs: list[Object]) -> list[Object]:
    """Creates linked duplicates for every object in the list.
    Replaces ancestor collections, and updates scene camera.
    """
    manifest: dict[Object, Object] = {obj: _action_copy_object(obj) for obj in objs}

    def _copy_col(col: Collection) -> Collection:
        new_col = bpy.data.collections.new(col.name)
        for obj in col.objects:
            new_col.objects.link(manifest.get(obj, obj))
        for child in col.children:
            if any(o in manifest for o in child.all_objects):
                new_col.children.link(_copy_col(child))
            else:
                new_col.children.link(child)
        return new_col

    for col in list(scene.collection.children):
        if any(o in manifest for o in col.all_objects):
            scene.collection.children.unlink(col)
            scene.collection.children.link(_copy_col(col))

    for obj in list(scene.collection.objects):
        if obj in manifest:
            scene.collection.objects.unlink(obj)
            scene.collection.objects.link(manifest[obj])

    scene.camera = manifest.get(scene.camera, scene.camera)
    return list(manifest.values())


# Main Functions / Public API
def action_copy_scene(context: Context, ref_scene: Scene, name: str) -> Scene:
    """Replace all animated objects in a scene and ancestor collections."""
    with context.temp_override(scene=ref_scene):
        bpy.ops.scene.new(type='LINK_COPY')

    new_scene: Scene = context.scene
    new_scene.name = name

    _apply_action_copy(
        new_scene,
        [obj for obj in new_scene.collection.all_objects if _obj_has_animation(obj)],
    )
    sync_system_update(context, force=True)
    return new_scene


def action_copy_object_in_scene(
    context: Context, scene: Scene, objs: list[Object]
) -> list[Object]:
    """Replace selected objects in a scene and ancestor collections."""
    new_objs = _apply_action_copy(scene, objs)
    sync_system_update(context, force=True)
    return new_objs
