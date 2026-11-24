"""
Instance Along Edges

Places a mesh object (or random picks from a collection) along the edges of
the selected mesh objects, using a Geometry Nodes modifier. Works on any
string of edges, including broken / disconnected chains: all chains are
treated as one continuous path, so spacing stays even across gaps.

Docs: docs/instance_along_edges.md in the AMP Tools repository.
"""

import bpy

from . import _common

GROUP_NAME = "Instance Along Edges"


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


# Bump when the node tree changes, so files built with an older version get
# their node group rebuilt (existing modifiers keep their settings).
GROUP_VERSION = 3
VERSION_KEY = _common.VERSION_KEY


def get_or_build_group():
    """Reuse the node group in this file if it is current, else (re)build it."""
    old = bpy.data.node_groups.get(GROUP_NAME)
    if old and old.get(VERSION_KEY) == GROUP_VERSION:
        return old
    ng = build_group(GROUP_NAME + ".new" if old else GROUP_NAME)
    if old:
        old.user_remap(ng)  # existing modifiers switch to the new tree
        bpy.data.node_groups.remove(old)
        ng.name = GROUP_NAME
    return ng


def build_group(name=GROUP_NAME):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng[VERSION_KEY] = GROUP_VERSION
    ng.is_modifier = True
    ng.description = "Place an object or collection along mesh edges"

    itf = ng.interface

    def inp(name, stype, default=None, mn=None, mx=None, desc=""):
        s = itf.new_socket(name, in_out="INPUT", socket_type=stype, description=desc)
        if default is not None:
            s.default_value = default
        if mn is not None:
            s.min_value = mn
        if mx is not None:
            s.max_value = mx
        return s

    itf.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    source_sock = inp("Source", "NodeSocketMenu", desc="Place a single object or pick from a collection")
    inp("Object", "NodeSocketObject", desc="Object to place along the edges")
    inp("Collection", "NodeSocketCollection", desc="Objects to place along the edges (random pick)")
    inp("Use Spacing", "NodeSocketBool", False,
                      desc="On: place by fixed distance. Off: fixed total count")
    inp("Count", "NodeSocketInt", 10, 1, 100000, "Total instances, spread evenly over the whole line")
    inp("Spacing", "NodeSocketFloat", 1.0, 0.001, 1e6, "Distance between instances, measured along the edges")
    inp("Offset", "NodeSocketFloat", 0.0, 0.0, 1e6, "Shift where the first instance lands along the line")
    inp("Align to Edges", "NodeSocketBool", True, desc="Rotate instances to follow the edge direction")
    inp("Rotation", "NodeSocketRotation", desc="Extra local rotation for every instance")
    inp("Scale", "NodeSocketFloat", 1.0, 0.0, 1e6)
    inp("Random Scale", "NodeSocketFloat", 0.0, 0.0, 1.0, "0 = uniform, 1 = scale varies from 0 to 2x")
    inp("Seed", "NodeSocketInt", 0)
    inp("Keep Edges", "NodeSocketBool", False, desc="Also output the original edge mesh")
    inp("Realize", "NodeSocketBool", False, desc="Convert instances to real geometry")
    itf.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    N, L = ng.nodes, ng.links

    def node(t, x, y, **props):
        n = N.new(t)
        n.location = (x, y)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    gi = node("NodeGroupInput", -1400, 0)
    go = node("NodeGroupOutput", 1400, 0)
    GI = gi.outputs

    # Mesh edges -> curve (internal only, user never touches curves)
    m2c = node("GeometryNodeMeshToCurve", -1150, 100)
    L.new(sock(GI, "Geometry"), m2c.inputs["Mesh"])

    # Treat every edge chain as part of ONE continuous path and sample it by
    # arc length across all chains. Spacing is then identical everywhere;
    # breaks in the line don't restart or stretch the spacing.
    def math(op, x, y, a=None, b=None, c=None):
        m = node("ShaderNodeMath", x, y, operation=op)
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        return m.outputs[0]

    total = node("GeometryNodeCurveLength", -850, 400)
    L.new(m2c.outputs["Curve"], total.inputs["Curve"])
    tot = total.outputs["Length"]

    # Count mode: spread Count instances evenly over the total length
    count_gap = math("DIVIDE", -600, 550, tot,
                     math("MAXIMUM", -850, 550, math("SUBTRACT", -1100, 550, sock(GI, "Count"), 1.0), 1.0))
    sw_sp = node("GeometryNodeSwitch", -350, 450, input_type="FLOAT")
    L.new(sock(GI, "Use Spacing"), sw_sp.inputs["Switch"])
    L.new(count_gap, sw_sp.inputs["False"])
    L.new(sock(GI, "Spacing"), sw_sp.inputs["True"])
    spacing = sw_sp.outputs[0]

    # number of points = floor((total - offset) / spacing) + 1, 0 if no edges
    usable = math("MAXIMUM", -600, 300, math("SUBTRACT", -850, 250, tot, sock(GI, "Offset")), 0.0)
    n = math("ADD", -100, 300,
             math("FLOOR", -350, 300, math("ADD", -350, 200, math("DIVIDE", -600, 150, usable, spacing), 1e-4)), 1.0)
    n = math("MULTIPLY", 100, 300, n, math("GREATER_THAN", -100, 450, tot, 0.0))

    # distance along the whole line for point i = Offset + i * spacing
    idx = node("GeometryNodeInputIndex", -600, 0)
    dist = math("MULTIPLY_ADD", -350, 0, idx.outputs[0], spacing, sock(GI, "Offset"))

    samp = node("GeometryNodeSampleCurve", -100, 0)
    set_menu(samp, "mode", "Mode", "Length")
    if hasattr(samp, "use_all_curves"):
        samp.use_all_curves = True
    else:
        sock(samp.inputs, "All Curves").default_value = True
    L.new(m2c.outputs["Curve"], sock(samp.inputs, "Curves"))
    L.new(dist, sock(samp.inputs, "Length"))

    pts = node("GeometryNodePoints", 150, 150)
    L.new(n, sock(pts.inputs, "Count"))
    L.new(sock(samp.outputs, "Position"), sock(pts.inputs, "Position"))
    sw_pts = pts  # points geometry feeding Instance on Points

    # +X follows the edge direction, +Z stays as close to world up as possible
    a2r = node("FunctionNodeAxesToRotation", 150, -150)
    set_menu(a2r, "primary_axis", "Primary Axis", "X")
    set_menu(a2r, "secondary_axis", "Secondary Axis", "Z")
    L.new(sock(samp.outputs, "Tangent"), sock(a2r.inputs, "Primary Axis"))
    sock(a2r.inputs, "Secondary Axis").default_value = (0.0, 0.0, 1.0)

    # Align toggle: edge rotation vs identity
    sw_rot = node("GeometryNodeSwitch", 350, -150, input_type="ROTATION")
    L.new(sock(GI, "Align to Edges"), sw_rot.inputs["Switch"])
    L.new(a2r.outputs[0], sw_rot.inputs["True"])

    # Collection -> instances (separate children so we can pick at random)
    coll = node("GeometryNodeCollectionInfo", -350, -400, transform_space="ORIGINAL")
    L.new(sock(GI, "Collection"), coll.inputs["Collection"])
    sock(coll.inputs, "Separate Children").default_value = True
    sock(coll.inputs, "Reset Children").default_value = True

    # Single object -> one instance (so Pick Instance always picks it)
    obj_info = node("GeometryNodeObjectInfo", -350, -650, transform_space="ORIGINAL")
    L.new(sock(GI, "Object"), obj_info.inputs["Object"])
    sock(obj_info.inputs, "As Instance").default_value = True

    # Source menu: Object / Collection
    src = node("GeometryNodeMenuSwitch", -100, -400, data_type="GEOMETRY")
    src.enum_items[0].name = "Object"
    src.enum_items[1].name = "Collection"
    L.new(sock(GI, "Source"), src.inputs["Menu"])
    L.new(obj_info.outputs["Geometry"], src.inputs["Object"])
    L.new(coll.outputs[0], src.inputs["Collection"])
    source_sock.default_value = "Object"

    rnd_idx = node("FunctionNodeRandomValue", -100, -550, data_type="INT")
    sock(rnd_idx.inputs, "Min", "INT").default_value = 0
    sock(rnd_idx.inputs, "Max", "INT").default_value = 100000
    L.new(sock(GI, "Seed"), sock(rnd_idx.inputs, "Seed"))

    # Random scale: Scale * random(1 - r, 1 + r)
    one_minus = node("ShaderNodeMath", -350, -750, operation="SUBTRACT")
    one_minus.inputs[0].default_value = 1.0
    L.new(sock(GI, "Random Scale"), one_minus.inputs[1])
    one_plus = node("ShaderNodeMath", -350, -900, operation="ADD")
    one_plus.inputs[0].default_value = 1.0
    L.new(sock(GI, "Random Scale"), one_plus.inputs[1])
    seed_off = node("ShaderNodeMath", -350, -1050, operation="ADD")
    L.new(sock(GI, "Seed"), seed_off.inputs[0])
    seed_off.inputs[1].default_value = 7919
    rnd_s = node("FunctionNodeRandomValue", -100, -800, data_type="FLOAT")
    L.new(one_minus.outputs[0], sock(rnd_s.inputs, "Min", "VALUE"))
    L.new(one_plus.outputs[0], sock(rnd_s.inputs, "Max", "VALUE"))
    L.new(seed_off.outputs[0], sock(rnd_s.inputs, "Seed"))
    mul_s = node("ShaderNodeMath", 150, -800, operation="MULTIPLY")
    L.new(sock(rnd_s.outputs, "Value", "VALUE"), mul_s.inputs[0])
    L.new(sock(GI, "Scale"), mul_s.inputs[1])

    iop = node("GeometryNodeInstanceOnPoints", 350, 100)
    L.new(sw_pts.outputs[0], iop.inputs["Points"])
    L.new(src.outputs[0], iop.inputs["Instance"])
    sock(iop.inputs, "Pick Instance").default_value = True
    L.new(sock(rnd_idx.outputs, "Value", "INT"), sock(iop.inputs, "Instance Index"))
    L.new(sw_rot.outputs[0], sock(iop.inputs, "Rotation"))
    L.new(mul_s.outputs[0], sock(iop.inputs, "Scale"))

    # Extra user rotation in local space
    rot_i = node("GeometryNodeRotateInstances", 600, 100)
    L.new(iop.outputs["Instances"], rot_i.inputs["Instances"])
    L.new(sock(GI, "Rotation"), sock(rot_i.inputs, "Rotation"))
    sock(rot_i.inputs, "Local Space").default_value = True

    rm = rot_i  # (no helper attributes to clean up)

    realize = node("GeometryNodeRealizeInstances", 1000, 250)
    L.new(rm.outputs[0], realize.inputs["Geometry"])
    sw_real = node("GeometryNodeSwitch", 1000, 100, input_type="GEOMETRY")
    L.new(sock(GI, "Realize"), sw_real.inputs["Switch"])
    L.new(rm.outputs[0], sw_real.inputs["False"])
    L.new(realize.outputs[0], sw_real.inputs["True"])

    # Keep original edges
    join = node("GeometryNodeJoinGeometry", 1200, 250)
    L.new(sw_real.outputs[0], join.inputs[0])
    L.new(sock(GI, "Geometry"), join.inputs[0])
    sw_keep = node("GeometryNodeSwitch", 1200, 50, input_type="GEOMETRY")
    L.new(sock(GI, "Keep Edges"), sw_keep.inputs["Switch"])
    L.new(sw_real.outputs[0], sw_keep.inputs["False"])
    L.new(join.outputs[0], sw_keep.inputs["True"])
    L.new(sw_keep.outputs[0], go.inputs[0])

    return ng


# --------------------------------------------------------------------------
# Operator
# --------------------------------------------------------------------------

class AMP_OT_instance_along_edges(bpy.types.Operator):
    """Add an Instance Along Edges modifier to the selected mesh objects"""

    bl_idname = "amp.instance_along_edges"
    bl_label = "Instance Along Edges"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _common.has_mesh_target(context)

    def execute(self, context):
        return _common.add_modifier(self, context, get_or_build_group(), GROUP_NAME,
                                    "set Object or Collection in the modifier")


TOOL = {
    "operator": AMP_OT_instance_along_edges.bl_idname,
    "label": "Instance Along Edges",
    "icon": "OUTLINER_OB_POINTCLOUD",
    "doc": "instance_along_edges.md",
}

classes = (AMP_OT_instance_along_edges,)
