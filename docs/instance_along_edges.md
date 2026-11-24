# Instance Along Edges

Places a mesh (or random picks from a collection) along the edges of a mesh object.
Use any string of edges as the path: no curve objects needed. Edit the edges in Edit
Mode and the placed meshes follow live.

## Quick start

1. Select the mesh whose edges form your line (you can select several).
2. Open the sidebar (**N**) in the 3D Viewport, go to the **AMP Tools** tab, and click
   **Instance Along Edges**.
3. In the new modifier (Properties > Modifiers), pick the **Object** to place.
4. Turn on **Use Spacing** and set **Spacing** for evenly spaced copies.

Clicking the button again on an object that already has the modifier just selects that
modifier; it doesn't add a second one.

## Inputs

| Input | What it does |
|---|---|
| **Source** | **Object**: place one mesh object. **Collection**: pick a random object from a collection at each point. |
| **Object** | The mesh to place (Source = Object). Its location in the scene doesn't matter; copies are placed by its origin. |
| **Collection** | Objects to choose from (Source = Collection). |
| **Use Spacing** | Off: place **Count** copies spread over the whole line. On: place a copy every **Spacing** units. |
| **Count** | Total number of copies along the whole line (Use Spacing off). |
| **Spacing** | Distance between copies, measured along the edges (Use Spacing on). |
| **Offset** | Slides every copy along the line. Handy when one lands awkwardly near a break. |
| **Align to Edges** | Rotates copies so their **+X** axis follows the edge and **+Z** stays as close to world up as possible. |
| **Rotation** | Extra rotation for every copy, in its own local space. Use it if your mesh's "forward" isn't +X. |
| **Scale** | Uniform scale for every copy. |
| **Random Scale** | 0 = all the same size; 1 = sizes vary from 0 to 2x **Scale**. |
| **Seed** | Changes the random picks (collection objects and random scale). |
| **Keep Edges** | Also show the original edges. |
| **Realize** | Turn the copies into real mesh, needed for export or for modifiers further down the stack. |

## How spacing works on broken lines

If your line has gaps (deleted segments) or several separate pieces, they are all treated
as **one continuous path**: the gaps themselves don't count toward the distance. That means:

- Spacing is exactly the same everywhere along the edges.
- Short pieces get fewer copies (possibly none) instead of being crammed.
- Copies don't always sit on the ends of each piece. Use **Offset** to nudge them.

## Tips

- **Vertical edges:** with Align to Edges on, "Z up" can't be satisfied on a perfectly
  vertical edge, so the twist around that edge may look arbitrary. Use **Rotation**, or turn
  off Align to Edges.
- **Updating:** when a new AMP Tools version changes this tool, clicking the button again
  upgrades the node group in your file. Existing modifiers keep their settings.
- The modifier uses a regular Geometry Nodes group named *Instance Along Edges*, so you can
  open it in the Geometry Nodes editor if you want to tweak it.
