# AMP Tools

A Blender extension that puts small production tools behind one-click buttons in the
3D Viewport sidebar (**N** > **AMP Tools**). Each button has a **?** next to it that
opens that tool's documentation.

Requires Blender 5.3 or newer.

## Tools

| Tool | What it does | Docs |
|---|---|---|
| Instance Along Edges | Places a mesh or collection along any string of mesh edges, with even spacing even across gaps. | [docs](docs/instance_along_edges.md) |
| Shrinkwrap Collection | Wraps a mesh onto the combined surface of every mesh in a collection, with an offset. | [docs](docs/shrinkwrap_collection.md) |

## Install

1. Build the extension zip (or download it from a release):
   ```bash
   mkdir -p dist && blender --command extension build --source-dir amp_tools --output-dir dist
   ```
2. In Blender: **Edit > Preferences > Get Extensions**, open the **⌄** menu at the top right,
   choose **Install from Disk...**, and pick `dist/amp_tools-<version>.zip`.

For development you can instead link the `amp_tools` folder into your
user extensions directory (`extensions/user_default/amp_tools`) and restart Blender.

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
4. Bump `version` in `amp_tools/blender_manifest.toml`.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
