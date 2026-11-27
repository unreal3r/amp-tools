"""Shared helpers for AMP Tools."""

import os

import bpy

VERSION_KEY = "amp_tools_version"
ID_KEY = "amp_tools_id"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def replace_group(old, new):
    """Point every user of `old` at `new`, delete `old`, and give `new` its name."""
    name = old.name
    old.user_remap(new)
    bpy.data.node_groups.remove(old)
    new.name = name


def get_bundled_group(blend_file, group_name, version):
    """
    Return AMP Tools' copy of `group_name`, appending it from assets/<blend_file>.

    AMP Tools copies are found by a tag, not by name. A current copy is reused;
    an older one is upgraded in place (modifiers keep their settings). A
    same-named group that AMP Tools didn't add is never touched.
    """
    existing = next((g for g in bpy.data.node_groups if g.get(ID_KEY) == group_name), None)
    if existing and existing.get(VERSION_KEY) == version:
        return existing

    path = os.path.join(ASSETS_DIR, blend_file)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.node_groups = [group_name]
    new = dst.node_groups[0]
    new[ID_KEY] = group_name
    new[VERSION_KEY] = version

    if existing:
        replace_group(existing, new)
    return new


def mesh_targets(context):
    targets = [o for o in context.selected_objects if o.type == "MESH"]
    if not targets and context.active_object and context.active_object.type == "MESH":
        targets = [context.active_object]
    return targets


def has_mesh_target(context):
    return bool(mesh_targets(context))


def add_modifier(operator, context, ng, label, hint):
    """Add a Geometry Nodes modifier using `ng` to each selected mesh (once)."""
    added = 0
    for obj in mesh_targets(context):
        mod = next((m for m in obj.modifiers if m.type == "NODES" and m.node_group == ng), None)
        if mod is None:
            mod = obj.modifiers.new(label, "NODES")
            mod.node_group = ng
            added += 1
        obj.modifiers.active = mod
    if added:
        operator.report({"INFO"}, f"Added {label} to {added} object(s); {hint}")
    else:
        operator.report({"INFO"}, f"{label} is already on the selected object(s)")
    return {"FINISHED"}


# ---- node-building helpers -------------------------------------------------

def sock(sockets, name, kind=None):
    """Find an available socket by name (optionally by socket type)."""
    for s in sockets:
        if s.name != name:
            continue
        if kind and s.type != kind:
            continue
        if getattr(s, "enabled", True) and getattr(s, "is_unavailable", False) is False:
            return s
    for s in sockets:  # fallback: ignore availability flags
        if s.name == name and (not kind or s.type == kind):
            return s
    raise KeyError(f"socket {name!r} ({kind}) not found in {[x.name for x in sockets]}")


def set_menu(node, prop, socket_name, value):
    """Set an option that is a node property in some versions and a menu socket in others."""
    if hasattr(node, prop):
        try:
            setattr(node, prop, value.upper())
            return
        except TypeError:
            pass
    s = sock(node.inputs, socket_name)
    s.default_value = value
