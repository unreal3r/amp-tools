"""AMP Tools: a sidebar panel of small production tools for Blender."""

import bpy

from .tools import MODULES

DOCS_URL = "https://github.com/unreal3r/amp-tools/blob/main/docs/"


class AMP_PT_tools(bpy.types.Panel):
    bl_label = "AMP Tools"
    bl_idname = "AMP_PT_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AMP Tools"

    def draw(self, context):
        col = self.layout.column(align=True)
        for module in MODULES:
            tool = module.TOOL
            row = col.row(align=True)
            row.operator(tool["operator"], text=tool["label"], icon=tool["icon"])
            help_op = row.operator("wm.url_open", text="", icon="QUESTION")
            help_op.url = DOCS_URL + tool["doc"]


def _all_classes():
    for module in MODULES:
        yield from module.classes
    yield AMP_PT_tools


def register():
    for cls in _all_classes():
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(list(_all_classes())):
        bpy.utils.unregister_class(cls)
