"""
In-Blender updates for AMP Tools, using Blender's own extension repositories.

The GitHub repo hosts `index.json` (a Blender extension repository listing).
"Set Up Updates" adds it as a remote repository (checked on startup) and moves
AMP Tools over to it; after that, "Check for Updates" (or Blender's own
update notice) installs new releases.
"""

import json
import os
import tomllib

import bpy

PKG_ID = "amp_tools"
REPO_NAME = "AMP Tools"
REPO_MODULE = "amp_tools_repo"
REPO_URL = "https://raw.githubusercontent.com/unreal3r/amp-tools/main/index.json"

_THIS_REPO = __package__.split(".")[1] if __package__.startswith("bl_ext.") else None


def find_repo():
    for i, repo in enumerate(bpy.context.preferences.extensions.repos):
        if repo.module == REPO_MODULE or repo.remote_url == REPO_URL:
            return i, repo
    return None, None


def is_set_up():
    return _THIS_REPO == REPO_MODULE


def local_version():
    path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)["version"]


def remote_version(repo):
    """Version listed in the repository's last synced index, or None."""
    path = os.path.join(repo.directory, ".blender_ext", "index.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    for pkg in data.get("data", []):
        if pkg.get("id") == PKG_ID:
            return pkg.get("version")
    return None


def _vtuple(v):
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def _need_online(op):
    if bpy.app.online_access:
        return False
    op.report({"WARNING"}, "AMP Tools needs Blender's online access to update: allow it in the popup "
                           "(or Preferences > System > Network > Allow Online Access)")
    try:
        bpy.ops.extensions.userpref_allow_online_popup("INVOKE_DEFAULT")
    except Exception:
        pass
    return True


def _sync(repo_index):
    bpy.ops.extensions.repo_sync(repo_index=repo_index)


def _deferred(func):
    """
    Run `func` once, after the current operator returns.

    `func` replaces this add-on, which is only safe once the calling operator
    has fully finished, so it always waits for a timer (in background mode,
    with no event loop, it never runs). Report first, then call this last.
    """
    def run():
        wm = bpy.context.window_manager
        if wm and wm.windows:
            with bpy.context.temp_override(window=wm.windows[0]):
                func()
        else:
            func()
        return None
    bpy.app.timers.register(run, first_interval=0.1)


def move_to_repo(old_repo_dir, new_repo_dir):
    """Uninstall the copy in `old_repo_dir`, install from `new_repo_dir`."""
    bpy.ops.extensions.package_uninstall(repo_directory=old_repo_dir, pkg_id=PKG_ID)
    bpy.ops.extensions.package_install(repo_directory=new_repo_dir, pkg_id=PKG_ID,
                                       enable_on_install=True)


def install_from(repo_dir):
    bpy.ops.extensions.package_install(repo_directory=repo_dir, pkg_id=PKG_ID,
                                       enable_on_install=True)


class AMP_OT_setup_updates(bpy.types.Operator):
    """Add the AMP Tools update repository and switch AMP Tools over to it (one time)"""

    bl_idname = "amp.setup_updates"
    bl_label = "Set Up Updates"

    def execute(self, context):
        if _need_online(self):
            return {"CANCELLED"}
        index, repo = find_repo()
        if repo is None:
            repo = context.preferences.extensions.repos.new(
                name=REPO_NAME, module=REPO_MODULE, remote_url=REPO_URL)
            index = len(context.preferences.extensions.repos) - 1
        repo.enabled = True
        repo.use_sync_on_startup = True
        _sync(index)
        if remote_version(repo) is None:
            self.report({"ERROR"}, f"Couldn't read the AMP Tools repository at {REPO_URL}")
            return {"CANCELLED"}
        if is_set_up():
            self.report({"INFO"}, "Updates are already set up")
            return {"FINISHED"}

        old_dir = next((r.directory for r in context.preferences.extensions.repos
                        if r.module == _THIS_REPO), None)
        new_dir = repo.directory
        context.preferences.is_dirty = True
        self.report({"INFO"}, "Updates set up: AMP Tools is reinstalling from its update repository")
        # last: this swaps out the running add-on
        if old_dir:
            _deferred(lambda: move_to_repo(old_dir, new_dir))
        else:
            _deferred(lambda: install_from(new_dir))
        return {"FINISHED"}


class AMP_OT_check_updates(bpy.types.Operator):
    """Check GitHub for a newer AMP Tools and install it"""

    bl_idname = "amp.check_updates"
    bl_label = "Check for Updates"

    def execute(self, context):
        if _need_online(self):
            return {"CANCELLED"}
        index, repo = find_repo()
        if repo is None:
            self.report({"WARNING"}, "Click Set Up Updates first")
            return {"CANCELLED"}
        _sync(index)
        remote, local = remote_version(repo), local_version()
        if remote is None:
            self.report({"ERROR"}, f"Couldn't read the AMP Tools repository at {REPO_URL}")
            return {"CANCELLED"}
        if _vtuple(remote) <= _vtuple(local):
            self.report({"INFO"}, f"AMP Tools {local} is up to date")
            return {"FINISHED"}
        repo_dir = repo.directory
        self.report({"INFO"}, f"Updating AMP Tools {local} -> {remote}")
        _deferred(lambda: install_from(repo_dir))  # last: replaces the running add-on
        return {"FINISHED"}


classes = (AMP_OT_setup_updates, AMP_OT_check_updates)
