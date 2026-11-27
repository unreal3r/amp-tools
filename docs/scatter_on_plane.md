# Scatter on Plane

Scatters a mesh (or random picks from a collection) over the faces of a mesh, with three
ways to control the distance between copies. Works on flat planes and on bumpy ground.

## Quick start

1. Select the mesh to scatter on (you can select several).
2. Open the sidebar (**N**) in the 3D Viewport, go to the **AMP Tools** tab, and click
   **Scatter on Plane**.
3. In the new modifier (Properties > Modifiers), pick the **Object** to scatter.
4. Pick a **Distribution** and set its distance.

Clicking the button again on an object that already has the modifier just selects that
modifier; it doesn't add a second one.

## Distribution: controlling the distance between copies

| Mode | Use it for | Settings |
|---|---|---|
| **Random** | Natural-looking scatter where nothing overlaps (rocks, trees, props). | **Minimum Distance**: no two copies are ever closer than this. The area fills up as densely as that allows. |
| **Grid** | Regular patterns: tiles, posts, planting rows. | **Grid Spacing**: distance between grid points. **Jitter**: shifts each point randomly, as a fraction of the spacing (0 = perfect grid, 1 = up to half a spacing either way). |
| **Density** | A set amount per area, where overlaps are fine (grass, debris). | **Density**: copies per square unit (per m² at the default unit scale). |

Only the settings for the chosen mode are used; Blender greys out the others.

## Other inputs

| Input | What it does |
|---|---|
| **Source** | **Object**: scatter one mesh object. **Collection**: pick a random object from a collection for each copy. |
| **Object** / **Collection** | What to scatter. The object's location in the scene doesn't matter; copies are placed by its origin. |
| **Seed** | Changes every random choice: positions, jitter, picks, spin and scale. |
| **Align to Surface** | On: each copy's **+Z** points along the surface normal (good for slopes). Off: copies stay upright. |
| **Random Rotation** | Random spin around each copy's own Z axis, from 0° up to this angle. 360° = fully random. |
| **Rotation** | Extra rotation for every copy, in its own local space. |
| **Position Offset** | Moves every copy in its own frame. With **Align to Surface** on, **Z** moves it along the surface normal (e.g. sink rocks slightly with a negative Z). **Scale** doesn't change the distance. |
| **Scale** / **Random Scale** | Size of the copies; Random Scale 0 = all the same, 1 = sizes vary from 0 to 2x **Scale**. |
| **Keep Surface** | Also show the surface (on by default). |
| **Realize** | Turn the copies into real mesh, needed for export or for modifiers further down the stack. |

## Tips

- **Grid on uneven ground:** grid points are laid out in the surface object's own X/Y and
  dropped straight down (its local -Z) onto the faces, so the spacing is even when seen from
  above. Points that miss the surface (holes, outside an irregular outline, or jittered
  past the outer edge) are skipped.
  To turn the grid, rotate the surface object.
- **Random mode and big areas:** a very small Minimum Distance on a very large surface
  makes a lot of copies; raise it first if Blender slows down.
- **Size of the copies vs. distance:** the distance is measured between the copies' origins.
  To stop large objects from touching, set Minimum Distance (or Grid Spacing) to at least
  their width.
- The modifier uses a regular Geometry Nodes group named *Scatter on Plane*, so you can
  open it in the Geometry Nodes editor if you want to tweak it.
