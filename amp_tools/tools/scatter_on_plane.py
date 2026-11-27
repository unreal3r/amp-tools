"""
Scatter on Plane

Scatters a mesh object (or random picks from a collection) over the faces of
the selected mesh, with three ways to control the distance between copies:

  Random   random positions, never closer than Minimum Distance
  Grid     a regular grid (Grid Spacing), optionally jittered, projected
           straight down (local -Z) onto the surface
  Density  pure random, a given number of copies per square unit

Docs: docs/scatter_on_plane.md in the AMP Tools repository.
"""

import math

import bpy

from . import _common
from ._common import sock, set_menu

GROUP_NAME = "Scatter on Plane"
# Bump when the node tree changes, so files built with an older version get
# their node group rebuilt (existing modifiers keep their settings).
GROUP_VERSION = 1
NORMAL_ATTR = "_amp_scatter_normal"


def get_or_build_group():
    old = next((g for g in bpy.data.node_groups if g.get(_common.ID_KEY) == GROUP_NAME), None)
    if old and old.get(_common.VERSION_KEY) == GROUP_VERSION:
        return old
    ng = build_group(GROUP_NAME + ".new" if old else GROUP_NAME)
    if old:
        _common.replace_group(old, ng)
    return ng


def build_group(name=GROUP_NAME):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng[_common.ID_KEY] = GROUP_NAME
    ng[_common.VERSION_KEY] = GROUP_VERSION
    ng.is_modifier = True
    ng.description = "Scatter an object or collection over a surface"
    itf = ng.interface

    def inp(name, stype, default=None, mn=None, mx=None, desc="", subtype=None):
        s = itf.new_socket(name, in_out="INPUT", socket_type=stype, description=desc)
        if subtype:
            s.subtype = subtype
        if default is not None:
            s.default_value = default
        if mn is not None:
            s.min_value = mn
        if mx is not None:
            s.max_value = mx
        return s

    itf.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    source_sock = inp("Source", "NodeSocketMenu", desc="Scatter a single object or pick from a collection")
    inp("Object", "NodeSocketObject", desc="Object to scatter")
    inp("Collection", "NodeSocketCollection", desc="Objects to scatter (random pick per copy)")
    dist_sock = inp("Distribution", "NodeSocketMenu",
                    desc="Random: never closer than Minimum Distance. Grid: regular grid with optional jitter. "
                         "Density: purely random, a number of copies per square unit")
    inp("Minimum Distance", "NodeSocketFloat", 1.0, 0.001, 1e6,
        "Random: copies are never closer than this", subtype="DISTANCE")
    inp("Grid Spacing", "NodeSocketFloat", 1.0, 0.001, 1e6, "Grid: distance between grid points", subtype="DISTANCE")
    inp("Jitter", "NodeSocketFloat", 0.0, 0.0, 1.0,
        "Grid: random shift of each point, as a fraction of the spacing (0 = perfect grid)", subtype="FACTOR")
    inp("Density", "NodeSocketFloat", 1.0, 0.0, 1e6, "Density: copies per square unit (e.g. per m²)")
    inp("Seed", "NodeSocketInt", 0, desc="Changes all random choices")
    inp("Align to Surface", "NodeSocketBool", True, desc="Point each copy's +Z along the surface normal")
    inp("Random Rotation", "NodeSocketFloat", 0.0, 0.0, math.tau,
        "Random spin around each copy's own Z axis, from 0 up to this angle", subtype="ANGLE")
    inp("Rotation", "NodeSocketRotation", desc="Extra rotation for every copy, in its own local space")
    inp("Position Offset", "NodeSocketVector", (0.0, 0.0, 0.0),
        desc="Move every copy in its own frame (Z = along the surface normal when aligned); "
             "not affected by Scale", subtype="TRANSLATION")
    inp("Scale", "NodeSocketFloat", 1.0, 0.0, 1e6)
    inp("Random Scale", "NodeSocketFloat", 0.0, 0.0, 1.0, "0 = uniform, 1 = scale varies from 0 to 2x", subtype="FACTOR")
    inp("Keep Surface", "NodeSocketBool", True, desc="Also output the surface the copies are scattered on")
    inp("Realize", "NodeSocketBool", False, desc="Convert copies to real geometry")
    itf.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    N, L = ng.nodes, ng.links

    def node(t, x, y, **props):
        n = N.new(t)
        n.location = (x, y)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(a, b):
        L.new(a, b)

    def math_(op, x, y, a=None, b=None, c=None):
        m = node("ShaderNodeMath", x, y, operation=op)
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                link(v, m.inputs[i])
        return m.outputs[0]

    gi = node("NodeGroupInput", -1800, 0)
    go = node("NodeGroupOutput", 1800, 0)
    GI = gi.outputs
    surface = sock(GI, "Geometry")

    def store_normal(geo, normal, x, y):
        st = node("GeometryNodeStoreNamedAttribute", x, y, data_type="FLOAT_VECTOR", domain="POINT")
        sock(st.inputs, "Name").default_value = NORMAL_ATTR
        link(geo, st.inputs["Geometry"])
        link(normal, sock(st.inputs, "Value", "VECTOR"))
        return st.outputs[0]

    # ---- Random: Poisson disk, never closer than Minimum Distance
    poisson = node("GeometryNodeDistributePointsOnFaces", -1300, 600)
    set_menu(poisson, "distribute_method", "Distribute Method", "Poisson")
    link(surface, poisson.inputs["Mesh"])
    link(sock(GI, "Minimum Distance"), sock(poisson.inputs, "Distance Min"))
    # enough candidates to fill the area: 4 per minimum-distance square
    d = math_("MAXIMUM", -1550, 500, sock(GI, "Minimum Distance"), 0.001)
    link(math_("DIVIDE", -1450, 450, 4.0, math_("MULTIPLY", -1500, 400, d, d)), sock(poisson.inputs, "Density Max"))
    link(sock(GI, "Seed"), sock(poisson.inputs, "Seed"))
    pts_random = store_normal(poisson.outputs["Points"], poisson.outputs["Normal"], -1050, 600)

    # ---- Density: plain random, Density per square unit
    dens = node("GeometryNodeDistributePointsOnFaces", -1300, 250)
    set_menu(dens, "distribute_method", "Distribute Method", "Random")
    link(surface, dens.inputs["Mesh"])
    link(sock(GI, "Density"), sock(dens.inputs, "Density"))
    link(sock(GI, "Seed"), sock(dens.inputs, "Seed"))
    pts_density = store_normal(dens.outputs["Points"], dens.outputs["Normal"], -1050, 250)

    # ---- Grid: grid over the bounding box in local XY, rays straight down
    bb = node("GeometryNodeBoundBox", -1550, -200)
    link(surface, bb.inputs["Geometry"])
    size = node("ShaderNodeVectorMath", -1350, -150, operation="SUBTRACT")
    link(bb.outputs["Max"], size.inputs[0]); link(bb.outputs["Min"], size.inputs[1])
    centre = node("ShaderNodeVectorMath", -1350, -300, operation="ADD")
    link(bb.outputs["Max"], centre.inputs[0]); link(bb.outputs["Min"], centre.inputs[1])
    size_xyz = node("ShaderNodeSeparateXYZ", -1200, -150)
    link(size.outputs["Vector"], size_xyz.inputs[0])
    sp = math_("MAXIMUM", -1350, -450, sock(GI, "Grid Spacing"), 0.001)

    def grid_axis(axis, y):
        count = math_("ADD", -900, y, math_("FLOOR", -1000, y, math_("ADD", -1050, y,
                      math_("DIVIDE", -1100, y, size_xyz.outputs[axis], sp), 1e-4)), 1.0)
        return count, math_("MULTIPLY", -800, y, math_("SUBTRACT", -850, y, count, 1.0), sp)

    nx, sx = grid_axis("X", -150)
    ny, sy = grid_axis("Y", -250)
    grid = node("GeometryNodeMeshGrid", -650, -200)
    link(sx, grid.inputs["Size X"]); link(sy, grid.inputs["Size Y"])
    link(nx, grid.inputs["Vertices X"]); link(ny, grid.inputs["Vertices Y"])

    # grid point -> centred on the bounding box, jittered, lifted above the top
    jit = node("FunctionNodeRandomValue", -650, -450, data_type="FLOAT_VECTOR")
    sock(jit.inputs, "Min", "VECTOR").default_value = (-0.5, -0.5, 0.0)
    sock(jit.inputs, "Max", "VECTOR").default_value = (0.5, 0.5, 0.0)
    link(math_("ADD", -800, -500, sock(GI, "Seed"), 17.0), sock(jit.inputs, "Seed"))
    jit_amt = math_("MULTIPLY", -650, -600, sock(GI, "Jitter"), sp)
    jit_v = node("ShaderNodeVectorMath", -450, -450, operation="SCALE")
    link(sock(jit.outputs, "Value", "VECTOR"), jit_v.inputs[0]); link(jit_amt, sock(jit_v.inputs, "Scale"))
    half_centre = node("ShaderNodeVectorMath", -1200, -300, operation="SCALE")
    link(centre.outputs["Vector"], half_centre.inputs[0]); sock(half_centre.inputs, "Scale").default_value = 0.5
    pos = node("GeometryNodeInputPosition", -650, -350)
    p1 = node("ShaderNodeVectorMath", -300, -350, operation="ADD")
    link(pos.outputs[0], p1.inputs[0]); link(half_centre.outputs["Vector"], p1.inputs[1])
    p2 = node("ShaderNodeVectorMath", -150, -400, operation="ADD")
    link(p1.outputs["Vector"], p2.inputs[0]); link(jit_v.outputs["Vector"], p2.inputs[1])
    p2_xyz = node("ShaderNodeSeparateXYZ", 0, -400)
    link(p2.outputs["Vector"], p2_xyz.inputs[0])
    max_xyz = node("ShaderNodeSeparateXYZ", -1200, -50)
    link(bb.outputs["Max"], max_xyz.inputs[0])
    top = node("ShaderNodeCombineXYZ", 150, -400)
    link(p2_xyz.outputs["X"], top.inputs["X"]); link(p2_xyz.outputs["Y"], top.inputs["Y"])
    link(math_("ADD", 0, -550, max_xyz.outputs["Z"], 1.0), top.inputs["Z"])
    m2p = node("GeometryNodeMeshToPoints", 300, -200)
    link(grid.outputs["Mesh"], m2p.inputs["Mesh"])
    link(top.outputs["Vector"], sock(m2p.inputs, "Position"))

    ray = node("GeometryNodeRaycast", 450, -450)
    link(surface, ray.inputs["Target Geometry"])
    # Points exactly on the surface's outer edge can miss by a rounding error,
    # so cast each ray from a hair (0.0001) toward the middle of the bounds.
    ray_pos = node("GeometryNodeInputPosition", 0, -700).outputs[0]
    to_mid = node("ShaderNodeVectorMath", 150, -700, operation="SUBTRACT")
    link(half_centre.outputs["Vector"], to_mid.inputs[0]); link(ray_pos, to_mid.inputs[1])
    to_mid_xy = node("ShaderNodeVectorMath", 250, -700, operation="MULTIPLY")
    link(to_mid.outputs["Vector"], to_mid_xy.inputs[0]); to_mid_xy.inputs[1].default_value = (1.0, 1.0, 0.0)
    nudge = node("ShaderNodeVectorMath", 350, -700, operation="NORMALIZE")
    link(to_mid_xy.outputs["Vector"], nudge.inputs[0])
    src_pos = node("ShaderNodeVectorMath", 450, -700, operation="MULTIPLY_ADD")
    link(nudge.outputs["Vector"], src_pos.inputs[0]); src_pos.inputs[1].default_value = (1e-4, 1e-4, 1e-4)
    link(ray_pos, src_pos.inputs[2])
    link(src_pos.outputs["Vector"], sock(ray.inputs, "Source Position"))
    sock(ray.inputs, "Ray Direction").default_value = (0.0, 0.0, -1.0)
    link(math_("ADD", 300, -600, size_xyz.outputs["Z"], 2.0), sock(ray.inputs, "Ray Length"))
    # keep hits only, then store the normal, then move onto the surface (each
    # step still evaluates the ray from the lifted position)
    miss = node("FunctionNodeBooleanMath", 600, -350, operation="NOT")
    link(ray.outputs["Is Hit"], miss.inputs[0])
    keep = node("GeometryNodeDeleteGeometry", 650, -200, domain="POINT")
    link(m2p.outputs["Points"], keep.inputs["Geometry"])
    link(miss.outputs[0], keep.inputs["Selection"])
    g_n = store_normal(keep.outputs[0], ray.outputs["Hit Normal"], 850, -200)
    onto = node("GeometryNodeSetPosition", 1000, -200)
    link(g_n, onto.inputs["Geometry"])
    link(ray.outputs["Hit Position"], sock(onto.inputs, "Position"))
    pts_grid = onto.outputs[0]

    # ---- Distribution menu
    dist_sw = node("GeometryNodeMenuSwitch", 1150, 300, data_type="GEOMETRY")
    dist_sw.enum_items[0].name = "Random"
    dist_sw.enum_items[1].name = "Grid"
    dist_sw.enum_items.new("Density")
    link(sock(GI, "Distribution"), dist_sw.inputs["Menu"])
    link(pts_random, dist_sw.inputs["Random"])
    link(pts_grid, dist_sw.inputs["Grid"])
    link(pts_density, dist_sw.inputs["Density"])
    dist_sock.default_value = "Random"
    points = dist_sw.outputs[0]

    # ---- What to place: Object or Collection
    coll = node("GeometryNodeCollectionInfo", 900, 700, transform_space="ORIGINAL")
    link(sock(GI, "Collection"), coll.inputs["Collection"])
    sock(coll.inputs, "Separate Children").default_value = True
    sock(coll.inputs, "Reset Children").default_value = True
    obj_info = node("GeometryNodeObjectInfo", 900, 950, transform_space="ORIGINAL")
    link(sock(GI, "Object"), obj_info.inputs["Object"])
    sock(obj_info.inputs, "As Instance").default_value = True
    src = node("GeometryNodeMenuSwitch", 1150, 800, data_type="GEOMETRY")
    src.enum_items[0].name = "Object"
    src.enum_items[1].name = "Collection"
    link(sock(GI, "Source"), src.inputs["Menu"])
    link(obj_info.outputs["Geometry"], src.inputs["Object"])
    link(coll.outputs[0], src.inputs["Collection"])
    source_sock.default_value = "Object"

    # ---- Orientation: +Z along the stored surface normal, or upright
    n_attr = node("GeometryNodeInputNamedAttribute", 1150, -100, data_type="FLOAT_VECTOR")
    sock(n_attr.inputs, "Name").default_value = NORMAL_ATTR
    align = node("FunctionNodeAlignRotationToVector", 1300, -100, axis="Z")
    link(sock(n_attr.outputs, "Attribute", "VECTOR"), sock(align.inputs, "Vector"))
    rot_sw = node("GeometryNodeSwitch", 1450, -100, input_type="ROTATION")
    link(sock(GI, "Align to Surface"), rot_sw.inputs["Switch"])
    link(align.outputs[0], rot_sw.inputs["True"])

    pick = node("FunctionNodeRandomValue", 1300, 500, data_type="INT")
    sock(pick.inputs, "Min", "INT").default_value = 0
    sock(pick.inputs, "Max", "INT").default_value = 100000
    link(math_("ADD", 1150, 450, sock(GI, "Seed"), 3.0), sock(pick.inputs, "Seed"))

    iop = node("GeometryNodeInstanceOnPoints", 1450, 300)
    link(points, iop.inputs["Points"])
    link(src.outputs[0], iop.inputs["Instance"])
    sock(iop.inputs, "Pick Instance").default_value = True
    link(sock(pick.outputs, "Value", "INT"), sock(iop.inputs, "Instance Index"))
    link(rot_sw.outputs[0], sock(iop.inputs, "Rotation"))

    # offset in the copy's own frame, before spin and scale
    trans = node("GeometryNodeTranslateInstances", 1600, 300)
    link(iop.outputs["Instances"], trans.inputs["Instances"])
    link(sock(GI, "Position Offset"), sock(trans.inputs, "Translation"))
    sock(trans.inputs, "Local Space").default_value = True

    # random spin around local Z
    spin_r = node("FunctionNodeRandomValue", 1450, 50, data_type="FLOAT")
    link(math_("ADD", 1300, 0, sock(GI, "Seed"), 29.0), sock(spin_r.inputs, "Seed"))
    spin_xyz = node("ShaderNodeCombineXYZ", 1700, 50)
    link(math_("MULTIPLY", 1600, 50, sock(spin_r.outputs, "Value", "VALUE"), sock(GI, "Random Rotation")),
         spin_xyz.inputs["Z"])
    spin_rot = node("FunctionNodeEulerToRotation", 1800, 50)
    link(spin_xyz.outputs[0], spin_rot.inputs[0])
    spin = node("GeometryNodeRotateInstances", 1750, 300)
    link(trans.outputs[0], spin.inputs["Instances"])
    link(spin_rot.outputs[0], sock(spin.inputs, "Rotation"))
    sock(spin.inputs, "Local Space").default_value = True

    user_rot = node("GeometryNodeRotateInstances", 1900, 300)
    link(spin.outputs[0], user_rot.inputs["Instances"])
    link(sock(GI, "Rotation"), sock(user_rot.inputs, "Rotation"))
    sock(user_rot.inputs, "Local Space").default_value = True

    # Scale * random(1 - r, 1 + r)
    scale_r = node("FunctionNodeRandomValue", 1750, -200, data_type="FLOAT")
    link(math_("SUBTRACT", 1600, -200, 1.0, sock(GI, "Random Scale")), sock(scale_r.inputs, "Min", "VALUE"))
    link(math_("ADD", 1600, -300, 1.0, sock(GI, "Random Scale")), sock(scale_r.inputs, "Max", "VALUE"))
    link(math_("ADD", 1600, -400, sock(GI, "Seed"), 7919.0), sock(scale_r.inputs, "Seed"))
    sc = node("GeometryNodeScaleInstances", 2050, 300)
    link(user_rot.outputs[0], sc.inputs["Instances"])
    link(math_("MULTIPLY", 1900, -200, sock(scale_r.outputs, "Value", "VALUE"), sock(GI, "Scale")),
         sock(sc.inputs, "Scale"))
    sock(sc.inputs, "Local Space").default_value = True

    rm = node("GeometryNodeRemoveAttribute", 2200, 300)
    link(sc.outputs[0], rm.inputs["Geometry"])
    sock(rm.inputs, "Name").default_value = NORMAL_ATTR

    realize = node("GeometryNodeRealizeInstances", 2350, 450)
    link(rm.outputs[0], realize.inputs["Geometry"])
    sw_real = node("GeometryNodeSwitch", 2350, 300, input_type="GEOMETRY")
    link(sock(GI, "Realize"), sw_real.inputs["Switch"])
    link(rm.outputs[0], sw_real.inputs["False"])
    link(realize.outputs[0], sw_real.inputs["True"])

    join = node("GeometryNodeJoinGeometry", 2500, 450)
    link(sw_real.outputs[0], join.inputs[0])
    link(surface, join.inputs[0])
    sw_keep = node("GeometryNodeSwitch", 2500, 300, input_type="GEOMETRY")
    link(sock(GI, "Keep Surface"), sw_keep.inputs["Switch"])
    link(sw_real.outputs[0], sw_keep.inputs["False"])
    link(join.outputs[0], sw_keep.inputs["True"])
    go.location = (2700, 300)
    link(sw_keep.outputs[0], go.inputs[0])
    return ng


class AMP_OT_scatter_on_plane(bpy.types.Operator):
    """Add a Scatter on Plane modifier to the selected mesh objects"""

    bl_idname = "amp.scatter_on_plane"
    bl_label = "Scatter on Plane"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _common.has_mesh_target(context)

    def execute(self, context):
        return _common.add_modifier(self, context, get_or_build_group(), GROUP_NAME,
                                    "set Object or Collection in the modifier")


TOOL = {
    "operator": AMP_OT_scatter_on_plane.bl_idname,
    "label": "Scatter on Plane",
    "icon": "PARTICLES",
    "doc": "scatter_on_plane.md",
}

classes = (AMP_OT_scatter_on_plane,)
