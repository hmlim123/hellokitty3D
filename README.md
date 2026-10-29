# Hello Kitty — pastel postcard animation

An editable Blender 4.3+ fan model with a plump pink bow and dress, daisy bouquet,
flat black oval eyes, and softly fused, thumb-free rounded paws. Warm cream whites, bright
rose backgrounds, and gentle contrast give it a nostalgic stationery/film-color
feel without adding grain. No external textures, add-ons or API keys are needed.

## Hawaiian hula animation

Open `hello_kitty_hawaiian_hula.blend` in Blender 4.3+ and press **Space**.
The editable eight-second loop runs on frames 1–480 at 60 fps, with hip sways,
gentle knee compression, shoulder-driven paw gestures, and 17 swaying skirt
panels. Feet stay planted; frame 481 matches the loop's starting pose and velocity.
[`hawaiian_hula_preview.png`](hawaiian_hula_preview.png) is a rendered pose preview.

The detailed `FIBERS` collection is hidden in the viewport for faster playback
and remains enabled for final renders. Use the named `CTRL_*` objects and Graph
Editor to adjust the dance. **Ctrl-F12** renders PNG frames to `hula_frames/`
beside the Blender file, at 1080 × 1350 with subtle motion blur.

To regenerate from the approved static model:

```sh
blender -b hello_kitty_hawaiian_plush_v2.blend --threads 4 --python-exit-code 1 --python animate_hawaiian_hula.py
```

Outputs go to `hawaiian_hula/`; `KITTY_HULA_OUTPUT_DIR` overrides this directory.
Add `-- --preview` to render a pose preview. Preserve edits before regenerating.

## Hawaiian plush — latest static version

Open `hello_kitty_hawaiian_plush_v2.blend` in Blender 4.3+. This is the approved
Hawaiian plush model with rounded ears, a larger head, fuller body and feet,
a flower crown, pink shell top, and green felt skirt. The matching portrait is
[`hawaiian_kitty_preview_v2.png`](hawaiian_kitty_preview_v2.png), at 1080 × 1350.

Select the named `CTRL_*` objects to pose the head, body, and paws. This model is
static; no animation is baked. Press **F12** to render, then choose **Image → Save
As** to export a PNG for Higgsfield. Hide the `FIBERS` collection for faster viewport
editing. Materials and geometry are self-contained; no add-ons are required.

To regenerate this version, run `blender -b --threads 4 --python-exit-code 1
--python create_hawaiian_kitty.py -- --render` from the repository directory.
Outputs go to `hawaiian_output/`; set `KITTY_OUTPUT_DIR` to use another directory.
The generator overwrites its outputs, so preserve any edits first.

## Open the postcard animation on your Mac

Open `hello_kitty_animated.blend` in Blender, move your pointer over the timeline,
and press **Space**. Frames 1–144 form a six-second loop at 24 fps. Timeline markers
identify the bounce, dance sway, wave, wink and flower offering. The static scene
is `hello_kitty.blend`. Use Rendered viewport shading and the active camera to
see the scene's intended lighting, or choose **Render → Render Image**.

The `ANIMATION` collection has named `CTRL_*` empties: root, body, head, two arms,
two feet and bouquet. Keys are editable in the Dope Sheet/Graph Editor. The wave
raises a thumb-free rounded paw and rotates its continuous arm around the shoulder; it doesn't translate the arm
away from the body. This is a rigid toy-style control rig, not a deforming skeletal
rig or a watertight mesh prepared for 3D printing.

## Why the dots are gone

Both scenes use Eevee with shadows and ray tracing disabled. The previous large
area-light shadows were still producing stochastic speckles at low sample counts.
The revised lighting uses deterministic surface shading and a decorative pastel
oval underfoot, trading realistic cast shadows for a clean illustrated-toy look.
The final video is 512 × 512 at 24 fps, with no added film grain. The nostalgic
feeling comes from the warm palette and soft contrast.

## Files

- `hello_kitty_animation.mp4`: rendered six-second motion loop.
- `hello_kitty_preview.png`: static portrait.
- `hello_kitty_wink.png`: wink-and-wave pose.
- `hello_kitty_three_quarter.png`: alternate camera showing volume.
- `create_hello_kitty.py`: builds the static scene.
- `animate_hello_kitty.py`: adds the control rig and animation.

## Rebuild

From `/workspace/hellokitty3D` in the cloud terminal:

```sh
XDG_CACHE_HOME=/tmp/kitty-mesa-cache blender -b --threads 5 --python-exit-code 1 --python create_hello_kitty.py -- --render
blender -b hello_kitty.blend --threads 5 --python-exit-code 1 --python animate_hello_kitty.py
```

The scripts overwrite generated Blender files; preserve your own edits first.
The static generator's `--render` renders the portrait. For the animated generator,
add `-- --preview --render` for the delivered 512px, 24 fps, 8-sample sequence,
or `-- --render` for 32 samples. Frames are written to `animation_frames/`.
Use a fresh frame directory so old renders are not mixed into the new video.

On your Mac, substitute `/Applications/Blender.app/Contents/MacOS/Blender` for
`blender`; the cache environment variable is only needed in the cloud container.
To encode the complete PNG sequence using FFmpeg:

```sh
ffmpeg -framerate 24 -i animation_frames/frame_%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart hello_kitty_animation.mp4
```

No server or background service is required. Cloud tasks already have an isolated
checkout; use it without creating a Git worktree. Keep the GitHub repository private.
