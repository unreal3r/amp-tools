"""AMP Tools: a sidebar panel of small production tools for Blender."""

import bpy

from . import updater
from .tools import MODULES

DOCS_URL = "https://github.com/unreal3r/amp-tools/blob/main/docs/"


def help_button(layout, page):
    layout.operator("wm.url_open", text="", icon="QUESTION").url = DOCS_URL + page


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
            help_button(row, tool["doc"])


class AMP_PT_updates(bpy.types.Panel):
    bl_label = "Updates"
    bl_idname = "AMP_PT_updates"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AMP Tools"
    bl_parent_id = "AMP_PT_tools"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text=f"Version {updater.local_version()}")
        row = col.row(align=True)
        if updater.is_set_up():
            row.operator("amp.check_updates", icon="FILE_REFRESH")
        else:
            row.operator("amp.setup_updates", icon="URL")
        help_button(row, "updates.md")


def _all_classes():
    for module in MODULES:
        yield from module.classes
    yield from updater.classes
    yield AMP_PT_tools
    yield AMP_PT_updates


def register():
    for cls in _all_classes():
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(list(_all_classes())):
        bpy.utils.unregister_class(cls)
