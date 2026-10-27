# Hello Kitty — pastel postcard animation

An editable Blender 4.3+ fan model with a plump pink bow and dress, daisy bouquet,
flat black oval eyes, and softly fused, thumb-free rounded paws. Warm cream whites, bright
rose backgrounds, and gentle contrast give it a nostalgic stationery/film-color
feel without adding grain. No external textures, add-ons or API keys are needed.

## Open on your Mac

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
