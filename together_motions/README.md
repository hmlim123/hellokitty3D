# Together performances

Seven separate editable projects append partner performances to the six Kitty
editions and My Melody. Original projects, old clip ranges, geometry and saved
progress are untouched. Each controller-only GLB reuses the game's existing
character mesh and preserves editable controls in its matching `.blend`.

The seven clips are `togetherWave`, `togetherHighfiveL`, `togetherHighfiveR`,
`togetherCelebrate`, `togetherStir`, `togetherDecorate` and `togetherPresent`.
They run at 24 fps; stirring/decorating last four seconds and the others three.
The appended ranges begin at frame 1501. Every clip returns to its empty-paw
rest and keeps the original foot controls planted throughout.

## Rebuild and export

From the repository root, with Blender 4.3.2:

```bash
for source in hello_kitty_natural.blend hello_kitty_plush_cloud.blend hello_kitty_plush_witch.blend hello_kitty_plush_baby.blend hello_kitty_plush_kitten.blend hello_kitty_plush_bunny.blend friends/melody.blend; do
  blender -b "$source" --python-exit-code 1 --python author_together_motions.py
done
```

To export an edited together project without rebuilding or saving over it:

```bash
blender -b together_motions/together_classic.blend --python-exit-code 1 --python export_together_motions.py
```

Each JSON records exact `.blend`, original source, author and exporter hashes,
normalization, original floor, clip ranges/durations, contact points and measured
baking grip bounds. The game receives only the seven `.glb`/`.json` pairs.

## Pair alignment

High-five actor anchors must be **0.84 world units apart**, facing one another.
Kitty's forward contact coordinate is 0.46; Melody's is 0.38. Both contact
surfaces are at height 0.72 and lateral offset 0.25. The host uses Kitty R and
the guest Melody L; the opposite hand pairing is also verified. Contact is at
one second and held through 1.25 seconds. `Together_Palm_L/R` are actual
relaxed paw surface points, separate from occupied tool grips.

The shoulder reaches gently forward while the curved relaxed paw straightens
by 14% along its length. Width stays unchanged, the upper caps remain attached
to Kitty's original pink shoulder or Melody's torso/lower hood, and head
translations remain at their original attached rest. The wider spacing also
keeps neutral heads clear during anticipation and return.

Runtime loaders with additive idle/walk pivot wrappers must subtract their bind
translations from the imported position tracks. Apply all imported scale and
rotation tracks. Kitty's arm mesh morphs must match the source: `Elbow_soft=0`,
`Paw_soft=0`, and `EmptyRest=1` for waves, high-fives and celebrations. For
occupied stirring, decorating and presenting, use `EmptyRest=1-envelope`.
The normalized envelope is
`smooth((t-.125)/(.333333-.125)) * (1-smooth((t-.416667)/(.875-.416667)))`,
where `smooth(x)` clamps x to [0,1] and returns `x*x*(3-2*x)`.
Controller-only GLBs do not contain these mesh morph tracks. Original occupied
grip geometry uses `Together_Grip_L/R`; baking JSON bounds measure those actual
animated grips. Source-only bouquet props are hidden by the preview renderer.

## Verification

```bash
for style in classic cloud witch baby kitten bunny melody; do
  blender -b "together_motions/together_${style}.blend" --python-exit-code 1 --python verify_together_motions.py
done
blender -b --python-exit-code 1 --python verify_together_pairs.py
blender -b --python-exit-code 1 --python verify_together_shoulders.py
blender -b together_motions/together_classic.blend --python-exit-code 1 --python render_together_motions.py
blender -b together_motions/together_classic.blend --python-exit-code 1 --python render_together_motions.py -- --neutral
```

Saved proofs cover 559 grounded source-frame samples per character, both
contacts over all seven held frames, and every clip's rest endpoint. Maximum
contact error is below 0.00000025 world units. All 73 frames of both hand roles
for all six Kitty editions versus Melody have disjoint actual head, hood,
accessory and torso geometry: 876 pair samples, minimum separating-plane gap
0.0284358 world units. A positive plane gap proves every mesh triangle is clear.
Both shared rigs retain intersecting upper-paw/shoulder support geometry at all
146 high-five frames per rig. Verifications are preserved beside the assets;
`highfive-partners.png` and `highfive-neutral.png` provide matching clean views.

These source checks establish Blender geometry and animation behavior. They do
not establish runtime integration or physical-device acceptance.
