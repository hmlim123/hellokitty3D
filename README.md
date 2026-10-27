# Hello Kitty in Blender

An editable, stylized fan model with a plump strawberry-pink bow, a rounded pink dress,
and a little pink-and-yellow daisy bouquet. The fuller cheeks, deeper head,
round tummy, and mitten hands give the character a soft collectible-toy shape.
Includes a display pedestal and a warm blush portrait scene. Made with Blender 4.3.2 using only built-in tools.
No add-ons, external textures, accounts, or API keys are needed for modeling.

## Open on your Mac

Download `hello_kitty.blend`, then open it in Blender 4.3 or newer using
**File → Open**. Press the Home key to frame the scene or use the saved camera
view. Render with **Render → Render Image**. The character and studio are in
separate collections; all character parts are named and editable. This is a
static model, without an animation rig or a watertight 3D-print mesh.

`hello_kitty_preview.png` shows the rendered portrait.
`hello_kitty_three_quarter.png` shows the depth from another camera angle.

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
uses 128 Cycles samples with denoising off. It works on the CPU.

No web server or background service is required. Cloud tasks already have an
isolated checkout; use the existing checkout without creating a Git worktree.

## Privacy

GitHub repository visibility is managed separately in repository settings.
Do not change visibility or publish assets elsewhere without authorization.

## Animated version

Open `hello_kitty_animated.blend`, then press **Space** over the timeline to
play. The 144-frame scene runs for six seconds at 24 fps. Timeline markers
identify the bounce, dance sway, wave, wink, and flower-offering gesture.

The `ANIMATION` collection contains named `CTRL_*` empty objects for posing:
root, body, head, two arms, two feet, and bouquet. This is a rigid toy-style
object rig, not a deforming skeletal rig. Animation keys remain editable in
the Dope Sheet and Graph Editor. The wink switches an oval eye to a curved
closed eye. All face pieces follow the head.

The animated scene uses **Eevee** to avoid Cycles sampling grain. The old
static portrait uses Cycles without denoising because this cloud build lacks
OpenImageDenoise. On a Mac Blender build supporting it, enabling **Render
Properties → Sampling → Render → Denoise** can clean up Cycles renders;
raising the sample count also reduces noise. For an editing view matching
the scene lighting, select Rendered viewport shading.

Rebuild the animated scene from the static source:

```sh
blender --background hello_kitty.blend --threads 5 --python-exit-code 1 --python animate_hello_kitty.py
```

Add `-- --render` to render all frames as PNGs in `animation_frames/`.
The delivered MP4 is a 400 × 400 preview sampled at 12 fps; the editable
Blender scene retains the full 24 fps animation and 640 × 640 render settings.
Render the full sequence on your Mac for a smoother, larger export.

To encode the full 24 fps PNG sequence using FFmpeg:

```sh
ffmpeg -framerate 24 -i animation_frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -movflags +faststart hello_kitty_animation.mp4
```

To reproduce the lightweight video preview instead, append `-- --preview --render`
to the animation build command, then encode the every-other-frame sequence:

```sh
ffmpeg -framerate 12 -pattern_type glob -i 'animation_frames/frame_*.png' -vf hqdn3d=2:1.5:3:2.25 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart hello_kitty_animation.mp4
```

Use a fresh or empty `animation_frames` directory when switching between full
and preview renders, so old frames are not mixed into the preview. The video
preview includes mild spatial/temporal noise reduction. `hello_kitty_wink.png`
is a rendered wink-and-wave pose.
