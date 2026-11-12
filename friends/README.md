# Three little friends for Nancy

Three independent, editable Blender 4.3 projects:

- **melody.blend** — My Melody: rose hood, soft bunny ears, ribbon and pink paw pads.
- **cinnamoroll.blend** — Cinnamoroll: ivory body, long floppy ears, blue embroidered face and curled cinnamon-roll tail.
- **kuromi.blend** — Kuromi: charcoal jester hood, round tip pompoms, pink skull badge and collar.

Open **friend_studio.blend** to see all three together. **dance-preview.mp4**
shows the three exported characters dancing in a six-second motion preview. The source files contain
smooth plush-inspired materials, rounded geometry and soft studio lighting.
They need no hair add-on or external texture. No character holds an item by default.

## Play expressions and gestures

The timeline runs at **24 fps**. Jump to a start frame and press **Space** to play.
Timeline markers identify the sections. Press **F12** to render the current pose.

| Performance | Frames | Useful still frame |
| --- | --- | --- |
| Gentle idle and blink | 1–97 | 1 |
| Wave | 121–193 | 147 |
| Happy dance | 217–361 | 260 |
| Polite bow | 385–457 | 421 |
| Celebrate | 481–577 | 517 |
| Self-hug / cuddle | 601–697 | 649 |
| Walk in place | 721–817 | 733 |
| Happy eyes | 841–913 | 877 |
| Wink | 937–985 | 961 |
| Sleepy | 1009–1105 | 1057 |
| Surprised | 1129–1201 | 1165 |
| Shy | 1225–1321 | 1273 |
| Curious | 1345–1441 | 1393 |

My Melody waves gently, Cinnamoroll waves with both paws and responsive ears,
and Kuromi adds a cheeky wink. Dance uses visible side steps, paw swings and hops.
The feet remain planted for bows and facial poses. Arms rest at the sides.

## Edit the models

Use the **CONTROLS — pose these** collection. Select CTRL_Root to move the whole
character; Body, Head, Arm, Foot and Ear controls pose the corresponding parts.
These are object controls, so an extra rigging add-on is unnecessary.

Select **Eye left**, **Eye right**, **Embroidered smile** or a **Pink cheek** mesh
and open **Object Data → Shape Keys**. Eye keys include Blink, SoftSmile, Sleepy,
Surprise, Shy and Curious; cheeks expose Warmth. The existing timeline animates
these values. Work at frame 1 for a neutral pose, or edit/add keys in a chosen clip.

**START HERE** text inside each project lists the controls and ranges. The STUDIO
collection is separate from the character. It is excluded from the GLB exports.

## Export an edited character on a Mac

Keep the export script and game_export_helpers folder next to the projects.
In Terminal, change to this folder, then run (replace melody with the character):

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b melody.blend --python-exit-code 1 --python export_friends.py
```

This exports **melody.glb** and **melody.json** beside the source. It does not
rebuild or save over hand edits. GLBs contain geometry, real morph targets and
13 named animation clips for future browser-game use. Idle and walk can loop;
the other performances return to rest. Integrating the new character identities
into Nancy's game is a separate step from authoring these source projects.

The create_friends.py script regenerates the source projects. Use export_friends.py
to preserve your own edits. create_preview_studio.py rebuilds the shared studio
and renders the illustrated expression and gesture sheets with `--sheets`.

## Verification

The three source projects and all 39 exported clips were checked in Blender 4.3.2.
Checks cover neutral empty-paw rests, outward ear surfaces, feet staying above the
floor, complete idle blinks, independent winks, each facial morph, visible dance
steps/hops, raised celebration paws and GLB/source checksums. The exports contain
about 20,000–30,000 triangles each and stay below 1.3 MB per character.

The GLBs were also loaded in Three.js/Chromium. All six facial poses, independent
winks and actual exported dance translations passed. The Blender expression and
gesture sheets were visually reviewed. The shared studio was reopened and checked
for linked-file or unpacked-image dependencies; it is self-contained.
