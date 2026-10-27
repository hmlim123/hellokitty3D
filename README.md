# Hello Kitty in Blender

An editable, stylized fan model with a red bow and dress, a display pedestal,
and a lit portrait scene. Made with Blender 4.3.2 using only built-in tools.
No add-ons, external textures, accounts, or API keys are needed for modeling.

## Open on your Mac

Download `hello_kitty.blend`, then open it in Blender 4.3 or newer using
**File → Open**. Press the Home key to frame the scene or use the saved camera
view. Render with **Render → Render Image**. The character and studio are in
separate collections; all character parts are named and editable. This is a
static model, without an animation rig or a watertight 3D-print mesh.

`hello_kitty_preview.png` shows the rendered scene.

## Rebuild

The generator rebuilds the entire scene; run it in a fresh Blender session.
It overwrites the generated blend and preview in this directory.

Cloud terminal, from `/workspace/hellokitty3D`:

```sh
blender --background --threads 6 --python-exit-code 1 --python create_hello_kitty.py -- --render
```

Mac terminal, from the downloaded project directory:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python create_hello_kitty.py -- --render
```

You can also open the Python file in Blender's Scripting workspace and run it
in a fresh session to generate and save the scene without rendering.
The cloud Blender build does not include OpenImageDenoise, so the generator
uses 96 Cycles samples with denoising off. It works on the CPU.

No web server or background service is required. Cloud tasks already have an
isolated checkout; use the existing checkout without creating a Git worktree.

## Privacy

These files were generated locally and have not been pushed to GitHub.
GitHub repository visibility is managed separately in repository settings.
