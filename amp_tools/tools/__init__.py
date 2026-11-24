"""
AMP Tools registry.

To add a tool: create a module (helpers in _common.py) in this folder that defines
  - `classes`: the bpy classes to register (at least one Operator)
  - `TOOL`: {"operator": bl_idname, "label": str, "icon": str, "doc": "page.md"}
then add the module to MODULES below and write docs/<page>.md.
"""

from . import instance_along_edges, shrinkwrap_collection

MODULES = (
    instance_along_edges,
    shrinkwrap_collection,
)
