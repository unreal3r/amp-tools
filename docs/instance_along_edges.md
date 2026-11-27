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
| **Count** | Total number of copies along the whole line (Use Spacing off). On a closed loop they're spread evenly all the way round. |
| **Spacing** | Distance between copies, measured along the edges (Use Spacing on). |
| **Start Offset** | Slides every copy along the line. Handy when one lands awkwardly near a break. (Called *Offset* before AMP Tools 0.3.0.) |
| **Align to Edges** | Off by default. When on, rotates copies so their **+X** axis follows the edge and **+Z** follows the line's "up" (see below). Fine-tune the result with **Rotation**. |
| **Rotation** | Extra rotation for every copy, in its own local space. Use it if your mesh's "forward" isn't +X. |
| **Position Offset** | Shifts the whole line the copies sit on, so you don't have to move the base mesh or the edges. **Y** moves it to the side (+Y is to the left when looking along the edge's direction) and **Z** moves it up; corners are mitered like an inset, so copies stay exactly that far from *every* edge, even at corners. **X** slides the copies along the line. Works with **Align to Edges** on or off; **Scale** doesn't change the distance. |
| **Scale** | Uniform scale for every copy. |
| **Random Scale** | 0 = all the same size; 1 = sizes vary from 0 to 2x **Scale**. |
| **Seed** | Changes the random picks (collection objects and random scale). |
| **Keep Edges** | Also show the original edges. |
| **Realize** | Turn the copies into real mesh, needed for export or for modifiers further down the stack. |

## How Position Offset handles corners

Y and Z don't push each copy away from its own edge; they build a new line parallel to
yours, like an inset (straight skeleton) would: each edge moves sideways by the same
distance and neighbouring edges meet on their angle bisector. Copies are then placed along
that new line, and **Spacing** is measured along it. So an inner corner doesn't bunch copies
up and an outer corner doesn't leave a gap.

- On a closed loop, whether +Y goes inside or outside depends on which way the loop runs.
  If it goes the wrong way, use a negative value.
- Very sharp corners are limited to 8x the offset distance so they can't shoot off to infinity.
- Offsetting inward by more than half the width of a shape makes the line cross over
  itself (a full straight skeleton would merge those edges instead).

## Which way is "up"

Align to Edges and Position Offset (Y/Z) need an "up" direction at every point. It's carried
smoothly along each piece of the line, turning only as much as the line bends, so it never
flips, even where the line runs straight up or down. Each piece is then turned as a whole so
that, where the line is closest to horizontal, up is world +Z. Flat lines therefore get plain
Z-up, and a loop hanging in a vertical plane keeps the same side facing out all the way round.

## How spacing works on broken lines

If your line has gaps (deleted segments) or several separate pieces, they are all treated
as **one continuous path**: the gaps themselves don't count toward the distance. That means:

- Spacing is exactly the same everywhere along the edges.
- Short pieces get fewer copies (possibly none) instead of being crammed.
- Copies don't always sit on the ends of each piece. Use **Start Offset** to nudge them.

## Tips

- **Placing copies beside or above the line:** use **Position Offset** instead of moving the
  object or its origin. For example, Y = 1.5 puts a row of posts 1.5 units to one side of a
  road edge, and -1.5 puts them on the other side.
- **Strings that go up and down** (hanging beads, loops round a pipe): "up" is carried smoothly
  along the line (a minimum-twist frame), so copies and offsets never flip over where the line
  passes through vertical.
- **Updating:** when a new AMP Tools version changes this tool, clicking the button again
  upgrades the node group in your file. Existing modifiers keep their settings.
- The modifier uses a regular Geometry Nodes group named *Instance Along Edges*, so you can
  open it in the Geometry Nodes editor if you want to tweak it.
