# Updating AMP Tools

AMP Tools updates from inside Blender, using Blender's own extension repository system
(the same one that powers **Get Extensions**). No more downloading zips.

## One-time setup

1. Open the **AMP Tools** tab in the 3D Viewport sidebar (**N**) and expand **Updates**.
2. Click **Set Up Updates**.
   - If Blender asks to **Allow Online Access**, say yes. (It's in
     Preferences > System > Network if you need it later.)
3. AMP Tools reinstalls itself from the AMP Tools update repository. This takes a second
   and the panel comes back. You'll find a new **AMP Tools** repository in
   Preferences > Get Extensions, set to check for updates when Blender starts.

## Getting updates

Either:

- Click **Check for Updates** in the **Updates** section. If there's a newer version it's
  installed right away; otherwise it tells you you're up to date.
- Or just start Blender: when an update is available, Blender shows an
  **extension updates available** notice in the status bar. Click it, then **Update**.

The **Updates** section always shows the version you have installed.

After an update, click a tool's button once in older files if the tool's notes say it
changed: the modifier upgrades and keeps all its settings.

## How it works

The GitHub repo hosts [`index.json`](../index.json), a listing in Blender's extension
repository format that points at the zip attached to the latest
[release](https://github.com/unreal3r/amp-tools/releases). Blender reads it, compares
versions, and downloads the zip. Nothing else is sent anywhere.

## Troubleshooting

- **"Couldn't read the AMP Tools repository"**: check your internet connection and that
  online access is allowed, then try again.
- **Two copies of AMP Tools in Get Extensions:** keep the one under the **AMP Tools**
  repository and uninstall the other (usually under **User Default**).
