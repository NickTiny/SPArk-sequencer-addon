# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy
from typing import List
from bpy.types import Context, Object, Collection, Event, Scene, ID
from spa_sequencer.utils import register_classes, unregister_classes
from spa_sequencer.sync.core import (
    get_sync_master_strip,
    get_sync_settings,
    remap_frame_value,
    sync_system_update,
)


class DOPESHEET_OT_sequence_navigate(bpy.types.Operator):
    bl_idname = "dopesheet.sequence_navigate"
    bl_label = "Navigate Sequence"
    bl_description = "Navigate master sequence"
    bl_options = {"UNDO", "BLOCKING", "INTERNAL"}

    frame: bpy.props.IntProperty(
        name="Frame",
        description="Frame value",
        default=-1,
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_settings().master_scene is not None

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        frame_value = int(
            context.region.view2d.region_to_view(event.mouse_region_x, 0)[0]
        )
        if frame_value != self.frame:
            self.frame = frame_value
            self.execute(context)

        # Validate
        if event.type in {"LEFTMOUSE"} and event.value in {"RELEASE"}:
            return {"FINISHED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context):
        master_scene = get_sync_settings().master_scene
        master_strip, _ = get_sync_master_strip()

        # Find a strip that matches the timing
        strips = [
            s
            for s in master_scene.sequence_editor.sequences
            if isinstance(s, bpy.types.SceneSequence) and s.scene == bpy.context.scene
        ]

        candidates = [
            s
            for s in strips
            if (
                remap_frame_value(s.frame_final_start, s)
                <= self.frame
                <= remap_frame_value(s.frame_final_end, s)
            )
        ]

        strip = next(
            (s for s in candidates if s == master_strip), next(iter(candidates), None)
        )

        # Update master scene current frame to enter target strip.
        if strip and strip != master_strip:
            master_scene.frame_set(strip.frame_final_start)

        # Set frame_current directly for context's active scene.
        # This proves to be enough and reacts better than frame_set which
        # might discard the change when playback is running.
        context.scene.frame_current = self.frame

        return {"FINISHED"}


class SEQUENCE_OT_active_shot_camera_set(bpy.types.Operator):
    bl_idname = "sequence.active_shot_camera_set"
    bl_label = "Set Active Shot Camera"
    bl_description = "Set active shot camera"
    bl_options = {"UNDO"}

    camera: bpy.props.StringProperty(
        name="Camera",
        description="Scene to set on active shot",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_master_strip(use_cache=True)[0] is not None

    def execute(self, context: bpy.types.Context):
        strip = get_sync_master_strip(use_cache=True)[0]
        cam = bpy.data.objects.get(self.camera, None)
        # Update strip's camera.
        strip.scene_camera = cam
        # Set this camera active in underlying scene.
        strip.scene.camera = cam
        return {"FINISHED"}


class SEQUENCE_OT_active_shot_scene_set(bpy.types.Operator):
    bl_idname = "sequence.active_shot_scene_set"
    bl_label = "Set Active Shot Scene"
    bl_description = "Set active shot scene"
    bl_options = {"UNDO"}

    scene: bpy.props.StringProperty(
        name="Scene",
        description="Scene to set on active shot",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_master_strip(use_cache=True)[0] is not None

    def execute(self, context: bpy.types.Context):
        strip = get_sync_master_strip(use_cache=True)[0]
        scene = bpy.data.scenes.get(self.scene, None)

        strip.scene = scene

        # Update strip's camera to use target scene's active camera.
        if not strip.scene_camera or (
            strip.scene_camera.name not in scene.collection.all_objects
        ):
            strip.scene_camera = scene.camera

        # Force sync system to update to account for this change.
        sync_system_update(context, force=True)
        return {"FINISHED"}


class SEQUENCE_OT_check_obj_users_scene(bpy.types.Operator):
    bl_idname = "sequence.check_obj_users_scene"
    bl_label = "Report Object use by Sequencer"
    bl_description = (
        "From the active object, report all sequencer strips using "
        "this object in their strip scenes"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and get_sync_master_strip(use_cache=True)[0]

    def build_obj_user_scene_report(self, obj):
        info_msg = ""
        master_scene = get_sync_settings().master_scene
        strips = [
            strip
            for strip in master_scene.sequence_editor.sequences_all
            if strip.type == "SCENE"
        ]

        for strip in sorted(strips, key=lambda f: f.frame_final_start):
            scene_msg = f" - Scene '{strip.scene.name}' from strips:\n"
            if scene_msg not in info_msg:
                info_msg += scene_msg
            info_msg += (
                f"   - {strip.name} "
                f"[{strip.frame_final_start}, {strip.frame_final_end}]\n"
            )

        report = f"Object '{obj.name}' is used in '{master_scene.name}' by:\n{info_msg}"
        return report

    def invoke(self, context, event):
        self.setup_name = context.scene.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        report = self.build_obj_user_scene_report(context.active_object)
        report_lines = report.split("\n")
        col = self.layout.column()
        for line in report_lines:
            col = self.layout.column()
            col.label(text=line)

    def execute(self, context: bpy.types.Context):
        report = self.build_obj_user_scene_report(context.active_object)
        self.report({"INFO"}, report)
        return {"FINISHED"}


class SEQUENCE_OT_copy_scene_strip_setup(bpy.types.Operator):
    bl_idname = "sequence.child_scene_setup_create"
    bl_label = "Duplicate Strip's Scene Setup"
    bl_description = "From the current scene, make a new scene either linked or full copy. Enables 'child scene'/'alt scene' workflows"
    bl_property = "setup_name"
    bl_options = {"UNDO"}

    # TODO Test linked objects

    _objects_map: dict = {}
    _collection_hirarchy: dict = {}
    _collection_map: dict = {}
    _suffix: str = ""

    @classmethod
    def poll(cls, context: Context):
        return get_sync_master_strip(use_cache=True)[0]

    setup_name: bpy.props.StringProperty(name="Name")  # type: ignore
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=(
            (
                "FULL_COPY",
                "Full Copy",
                "Create a full copy of the current scene, creating an 'Alternate Scene'",
            ),
            (
                "ACTION_COPY",
                "Action Copy",
                "Create a linked copy of static objects a 'full' copy of animated objects",
            ),
            (
                "LINK_COPY",
                "Linked Copy",
                "Create a linked copy of the current scene, creating an 'Child Scene' (adds new collection)",
            ),
        ),
    )  # type: ignore

    def invoke(self, context: Context, event: Event) -> set:
        self.setup_name = context.scene.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.prop(self, "mode", expand=False)
        layout.prop(self, "setup_name")

    def execute(self, context: Context) -> set:
        # Cancel if user provides a scene name that is already used
        if self.setup_name in bpy.data.scenes:
            self.report({"ERROR"}, "Name already in use")
            return {"CANCELLED"}
        # Get current strip it's scene as a reference
        strip = get_sync_master_strip(use_cache=True)[0]
        ref_scene = strip.scene
        camera = strip.scene_camera

        if camera and self.mode == "FULL_COPY":
            camera["temp_scene_strip"] = strip.name

        # Create new Scene and set name
        with context.temp_override(scene=ref_scene):
            # Action Copy are linked scenes to start with
            if self.mode == "ACTION_COPY":
                mode = "LINK_COPY"
            else:
                mode = self.mode

            bpy.ops.scene.new(type=mode)
        new_scene = context.scene
        new_scene.name = self.setup_name
        # create pointer back to old scene
        new_scene.parent_scene = ref_scene

        if self.mode == "LINK_COPY":
            # Create new collection with the same name
            new_setup_collection = bpy.data.collections.new(name=self.setup_name)
            new_scene.collection.children.link(new_setup_collection)

        if self.mode == "ACTION_COPY":
            self.replace_action_collection_with_copy(new_scene)

        if self.mode == "FULL_COPY":
            for obj in new_scene.objects:
                if getattr(obj, '["temp_scene_strip"]', None) == strip.name:
                    strip.scene_camera = obj

                    # Clear Property after finding duplicated camera
                    del obj["temp_scene_strip"]
                    del camera["temp_scene_strip"]

        # Assign new scene to current strip
        strip.scene = new_scene

        # Report to user new scene creation and assignment
        self.report(
            {"INFO"},
            f"New scene setup '{self.setup_name}' created on strip '{strip.name}'",
        )
        return {"FINISHED"}

    def replace_action_collection_with_copy(self, new_scene: Scene) -> None:
        action_cols = set()
        scene_col = new_scene.collection
        self._suffix = new_scene.name
        # Reset Maps
        self._objects_map = {}
        self._collection_hirarchy = {}
        self._collection_map = {}

        # Find Action Collections to Copy
        for collection in scene_col.children_recursive:
            if self.is_action_collection(collection):
                action_cols.add(collection)
                self.create_object_copies(collection)

        # for top_col in scene_col.children:
        # Get a list of all collections that are parents of action collection
        self.recursively_find_collection_hirarchy(
            scene_col, action_cols, self._collection_hirarchy
        )

        self.recursively_copy_collection_hirarchy(scene_col, self._collection_hirarchy)

        self.reaplce_objects_via_map(scene_col)
        for col in scene_col.children_recursive:
            self.reaplce_objects_via_map(col)

    def reaplce_objects_via_map(self, collection: Collection) -> None:
        for obj in collection.objects:
            if not self._objects_map.get(obj.name):
                continue
            target_obj = bpy.data.objects.get(self._objects_map[obj.name])
            collection.objects.unlink(obj)
            collection.objects.link(target_obj)

    def create_object_copies(self, collection: Collection) -> None:
        copied_actions = {}
        for object in collection.objects:

            # Skip non-action objects
            if not self.is_action_object(object):
                continue

            # Skip object if it was already reaplced
            if object.name in list(self._objects_map.values()):
                continue

            if not self._objects_map.get(object.name):
                obj_copy = self.copy_datablock(object)
                self._objects_map[object.name] = obj_copy.name
            else:
                obj_copy = bpy.data.objects.get(self._objects_map[object.name])

            obj_copy_action = obj_copy.animation_data.action
            if obj_copy_action:
                if not copied_actions.get(obj_copy_action):
                    action_copy = self.copy_datablock(obj_copy_action)
                    copied_actions[obj_copy_action] = action_copy
                obj_copy.animation_data.action = copied_actions[obj_copy_action]

            for nla_track in obj_copy.animation_data.nla_tracks:
                for nla_strip in nla_track.strips:
                    if not copied_actions.get(nla_strip.action):
                        action_copy = self.copy_datablock(nla_strip.action)
                        copied_actions[nla_strip.action] = action_copy

                    nla_strip.action = copied_actions[nla_strip.action]

    def copy_datablock(self, datablock: ID) -> ID:
        new_name = self.get_name(datablock.name)
        copied_datablock = datablock.copy()
        copied_datablock.name = new_name
        return copied_datablock

    def get_name(self, basename: str) -> str:
        return basename + "-" + self._suffix

    def recursively_copy_collection_hirarchy(
        self, scene_col: bpy.types.Scene, map: dict
    ) -> None:
        for parent_name, targets in map.items():
            for target_name in targets.keys():
                self.copy_collection_in_place(scene_col, parent_name, target_name)

            self.recursively_copy_collection_hirarchy(scene_col, map[parent_name])

    def recursively_find_collection_hirarchy(
        self,
        parent_col: bpy.types.Collection,
        target_cols: List[bpy.types.Collection],
        map: dict,
    ) -> None:

        for target_col in target_cols:
            if target_col == parent_col:
                if not map.get(parent_col.name):
                    map[target_col.name] = {}

            if target_col in list(parent_col.children):
                if not map.get(parent_col.name):
                    map[parent_col.name] = {}

                map[parent_col.name].update({target_col.name: {}})

        for collection in parent_col.children:
            for target_col in target_cols:
                if target_col in list(collection.children_recursive):
                    if not map.get(parent_col.name):
                        map[parent_col.name] = {}
                    map[parent_col.name].update({collection.name: {}})
                    self.recursively_find_collection_hirarchy(
                        collection, target_cols, map[parent_col.name]
                    )

    def is_action_collection(self, collection: Collection) -> bool:
        for object in collection.objects:
            if object.animation_data:
                # TODO Also if its an armature do this
                return True
        return False

    def is_action_object(self, object: Object) -> bool:
        if object.type == "ARMATURE":
            return True
        return bool(object.animation_data)

    def copy_collection_in_place(
        self, scene_col: Collection, parent_name: str, source_name: str
    ) -> None:
        parent_col = self.get_mapped_collection(scene_col, parent_name)
        target_col = self.get_mapped_collection(scene_col, source_name)
        source_col = bpy.data.collections.get(source_name)
        parent_col.children.unlink(source_col)
        parent_col.children.link(target_col)

    def get_mapped_collection(
        self, scene_col: Collection, collection_name: str
    ) -> Collection:
        if collection_name == "Scene Collection":
            return scene_col

        if not self._collection_map.get(collection_name):
            source_col = bpy.data.collections.get(collection_name)
            target_col = self.copy_datablock(source_col)
            self._collection_map[collection_name] = target_col.name
            return target_col
        else:
            return bpy.data.collections.get(self._collection_map[collection_name])


classes = (
    SEQUENCE_OT_check_obj_users_scene,
    DOPESHEET_OT_sequence_navigate,
    SEQUENCE_OT_active_shot_camera_set,
    SEQUENCE_OT_active_shot_scene_set,
    SEQUENCE_OT_copy_scene_strip_setup,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
