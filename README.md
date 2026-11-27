# AMP Tools

A Blender extension that puts small production tools behind one-click buttons in the
3D Viewport sidebar (**N** > **AMP Tools**). Each button has a **?** next to it that
opens that tool's documentation.

Requires Blender 5.3 or newer.

## Tools

| Tool | What it does | Docs |
|---|---|---|
| Instance Along Edges | Places a mesh or collection along any string of mesh edges, with even spacing even across gaps. | [docs](docs/instance_along_edges.md) |
| Scatter on Plane | Scatters a mesh or collection over a surface: random with a minimum distance, a jittered grid, or a density per m². | [docs](docs/scatter_on_plane.md) |
| Shrinkwrap Collection | Wraps a mesh onto the combined surface of every mesh in a collection, with an offset. | [docs](docs/shrinkwrap_collection.md) |

## Install

1. Download `amp_tools-<version>.zip` from the latest
   [release](https://github.com/unreal3r/amp-tools/releases).
2. In Blender: **Edit > Preferences > Get Extensions**, open the **⌄** menu at the top right,
   choose **Install from Disk...**, and pick the zip.
3. In the 3D Viewport sidebar (**N**), open **AMP Tools > Updates** and click
   **Set Up Updates** once. From then on, updates install from inside Blender
   ([how updates work](docs/updates.md)).

For development you can instead link the `amp_tools` folder into your
user extensions directory (`extensions/user_default/amp_tools`) and restart Blender.

## Releasing a new version

1. Bump `version` in `amp_tools/blender_manifest.toml`.
2. Run `scripts/build_release.sh /path/to/blender`. It builds `dist/amp_tools-<version>.zip`
   and regenerates `index.json` to point at the matching GitHub release.
3. Commit (including `index.json`), push, and create release `v<version>` with the zip
   attached. Blender picks up the update as soon as both are on GitHub.

## Adding a tool

1. Add a module in `amp_tools/tools/` that defines `classes` (at least one operator)
   and a `TOOL` dict: `{"operator", "label", "icon", "doc"}`. Helpers live in
   `amp_tools/tools/_common.py`.
   - **Node group built in Python:** see `instance_along_edges.py`.
   - **Existing node group from a .blend:** save just that group into
     `amp_tools/assets/<tool>.blend` and load it with `_common.get_bundled_group()`;
     see `shrinkwrap_collection.py`. Bump the tool's `GROUP_VERSION` whenever you
     replace the .blend, so files using the old copy get upgraded.
2. Add it to `MODULES` in `amp_tools/tools/__init__.py`.
3. Write `docs/<tool>.md` and list it in `docs/README.md` and the table above.
4. Release it (see above).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
