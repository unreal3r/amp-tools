"""
Shrinkwrap Collection

Snaps every vertex of the selected meshes onto the nearest surface of all the
meshes in a target collection (combined), then pushes it back out by Offset,
along the surface normal or along the direction it snapped from.

The node group ships as assets/shrinkwrap_collection.blend and is appended
into the file the first time the button is used.

Docs: docs/shrinkwrap_collection.md in the AMP Tools repository.
"""

import bpy

from . import _common

GROUP_NAME = "ShrinkwrapCollection"
BLEND_FILE = "shrinkwrap_collection.blend"
# Bump when assets/shrinkwrap_collection.blend changes
GROUP_VERSION = 1


class AMP_OT_shrinkwrap_collection(bpy.types.Operator):
    """Add a Shrinkwrap Collection modifier to the selected mesh objects"""

    bl_idname = "amp.shrinkwrap_collection"
    bl_label = "Shrinkwrap Collection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _common.has_mesh_target(context)

    def execute(self, context):
        ng = _common.get_bundled_group(BLEND_FILE, GROUP_NAME, GROUP_VERSION)
        return _common.add_modifier(self, context, ng, "Shrinkwrap Collection",
                                    "set Target Collection in the modifier")


TOOL = {
    "operator": AMP_OT_shrinkwrap_collection.bl_idname,
    "label": "Shrinkwrap Collection",
    "icon": "MOD_SHRINKWRAP",
    "doc": "shrinkwrap_collection.md",
}

classes = (AMP_OT_shrinkwrap_collection,)
