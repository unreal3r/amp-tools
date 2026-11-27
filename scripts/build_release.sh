#!/usr/bin/env bash
# Build the extension zip and regenerate index.json (the update repository
# listing Blender reads) so it points at this version's GitHub release asset.
#
# Usage:  scripts/build_release.sh [path/to/blender]
# Then:   commit index.json, push, and create release v<version> with
#         dist/amp_tools-<version>.zip attached (the index links to it).
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${1:-blender}"
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' amp_tools/blender_manifest.toml)
ZIP="amp_tools-${VERSION}.zip"

# Keep the build away from your real Blender settings and add-ons
export BLENDER_USER_RESOURCES="$(mktemp -d)"

mkdir -p dist
"$BLENDER" --factory-startup --command extension build --source-dir amp_tools --output-dir dist

REPO_DIR="$(mktemp -d)"
cp "dist/${ZIP}" "$REPO_DIR/"
"$BLENDER" --factory-startup --command extension server-generate --repo-dir="$REPO_DIR"

python3 - "$REPO_DIR/index.json" "$VERSION" "$ZIP" <<'PY'
import json, sys
src, version, zip_name = sys.argv[1:]
data = json.load(open(src))
for pkg in data["data"]:
    pkg["archive_url"] = f"https://github.com/unreal3r/amp-tools/releases/download/v{version}/{zip_name}"
json.dump(data, open("index.json", "w"), indent=2)
open("index.json", "a").write("\n")
PY
echo "Built dist/${ZIP} and index.json for v${VERSION}"
