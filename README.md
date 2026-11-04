# Hello Kitty — pastel postcard animation

An editable Blender 4.3+ fan model with a plump pink bow and dress, daisy bouquet,
flat black oval eyes, and softly fused, thumb-free rounded paws. Warm cream whites, bright
rose backgrounds, and gentle contrast give it a nostalgic stationery/film-color
feel without adding grain. No external textures, add-ons or API keys are needed.

## Game edition · November 2026

Open **`hello_kitty_game.blend`** for the game work. The original static and
six-second animated files remain unchanged. This new file adds editable rigid
performances, two friends, and ten prop assemblies (including three cutter
shapes). All materials are self-contained; no add-ons or textures are required.

| Named performance | Timeline at 24 fps | Game use |
| --- | --- | --- |
| Dance / Wave / Offer | 1–140 | Existing room buttons and flower offering |
| Stir | 145–217 | Mixing dough |
| Cut | 217–265 | Pressing Nancy's cutter |
| Present | 265–313 | Holding her decorated cookie tray |
| Surprise | 313–349 | Discovering an item |
| Bow | 349–391 | A happy thank-you |
| Celebrate | 391–451 | Completing a quest |
| Sip | 451–511 | Lifting a teacup |

Use timeline markers to find each performance. `CTRL_*` empties remain the
editable toy controls; paws stay connected to their shoulder pivots. The
`Socket_Paw_L/R`, `Socket_Teacup` and `Socket_Tray` empties are attachment points.
The tray's midpoint uses two Copy Location constraints. These are rigid toy
motions, not a deforming armature with finger articulation.

- **GAME — friends:** Momo and Pip, each with a two-second greeting on frames
  1–49. Select `Momo_Paw_L` or `Pip_Ear_L/R` to edit the keyed motions.
- **GAME — cozy props:** cushion, frame, oven, tray, teacup, dough bowl, wooden
  spoon, and round/heart/star cutters. Assemblies sit beside the character for
  editing; the game centers each root when exporting.
- **GAME — authoring preview:** held spoon, cutter, tray and cup appear during
  the relevant timeline section. This preview is excluded from the web export.
  Nancy's actual icing and sprinkles are composed by the browser game.

Rebuild only the game edition from the original animated file:

```sh
blender -b hello_kitty_animated.blend --python-exit-code 1 --python create_game_assets.py
```

The command replaces `hello_kitty_game.blend`; save manual changes to a separate
working copy first. To export your edited working copy from `hellokittygame`:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" \
  -b ../hellokitty3D/hello_kitty_game.blend --python-exit-code 1 \
  --python scripts/export_blender.py
npm run dev
```

The game exporter writes `hello-kitty.glb`, `cozy-friends.glb`, `cozy-props.glb`
and source provenance. It preserves your input `.blend`, excludes the studio,
reduces the character mesh, converts the wink to morph targets, and produces
independent named clips. Preserve object/controller names when editing so the
existing game events keep working. Game lighting is defined separately in Three.js.

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
