import bpy

from ...utils import register_classes, unregister_classes
from .ops import IMPORT_OT_otio, EXPORT_OT_otio

class SEQUENCER_MT_edit_io(bpy.types.Menu):
    bl_idname = "SEQUENCER_MT_edit_io"
    bl_label = "Timeline I/O"

    def draw(self, context):
        self.layout.operator(IMPORT_OT_otio.bl_idname, text="Import Timeline...")
        self.layout.operator(EXPORT_OT_otio.bl_idname, text="Export Timeline...")


classes = (SEQUENCER_MT_edit_io,)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
