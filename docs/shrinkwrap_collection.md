# Shrinkwrap Collection

Wraps a mesh onto the **combined surface of every mesh in a collection**, like the
Shrinkwrap modifier but with a whole collection as the target instead of one object.
Useful for draping a cover, decal mesh or cage over a group of separate pieces.

## Quick start

1. Put the meshes you want to wrap onto in a collection.
2. Select the mesh to be wrapped (you can select several).
3. Open the sidebar (**N**) in the 3D Viewport, go to the **AMP Tools** tab, and click
   **Shrinkwrap Collection**.
4. In the new modifier (Properties > Modifiers), pick the **Target Collection**.
5. Raise **Offset** a little to keep the wrapped mesh from z-fighting with the target.

Clicking the button again on an object that already has the modifier just selects that
modifier; it doesn't add a second one.

## Inputs

| Input | What it does |
|---|---|
| **Target Collection** | The meshes to wrap onto. All objects in it are combined into one target surface. |
| **Offset** | How far to push the wrapped surface back out from the target. |
| **Offset Mode** | **Surface Normals**: push along the target's surface normal (even thickness, follows the target's shape). **Snap Direction**: push back toward where each vertex came from (keeps more of the original shape's flow). |

## How it works

Each vertex snaps to the nearest point on the target's faces, then moves out by **Offset**
in the chosen direction. Vertices are moved, never added or removed, so the wrapped mesh
keeps its topology and UVs. Denser meshes follow the target more closely.

## Tips

- **Target transforms:** the target objects' locations, rotations and scales are respected,
  so you can move the targets around and the wrap follows.
- **Snap Direction and touching vertices:** a vertex that already sits exactly on the target
  has no snap direction, so Offset can't push it out in that mode. Use Surface Normals there.
- **Stacking:** put a Subdivision Surface modifier *above* this one for a smoother wrap, or
  *below* it to smooth the result.
- The modifier uses a Geometry Nodes group named *ShrinkwrapCollection*, so you can open it
  in the Geometry Nodes editor. If you already appended your own copy into a file, AMP Tools
  leaves it alone and adds its own copy next to it.
