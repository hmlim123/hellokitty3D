"""Polish the existing natural edition without adding activities.
blender -b hello_kitty_natural.blend --python-exit-code 1 --python refine_natural_flow.py
"""
import bpy
import math
import json
from mathutils import Vector
from pathlib import Path

s = bpy.context.scene
s.frame_set(1)
# Give the stir clip its own closing contact frame before Cut begins at 217.
# Adjacent clips must not overwrite the endpoint of a continuous spoon loop.
controls = list(bpy.data.collections['ANIMATION — select controls to pose'].objects)
s.frame_set(145)
transforms = [(o, o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for o in controls]
morphs = [(key, key.value) for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys for key in o.data.shape_keys.key_blocks if key.name in ['Elbow_soft', 'Paw_soft']]
s.frame_set(216)
for o, location, rotation, scale in transforms:
    o.location = location;o.rotation_euler = rotation;o.scale = scale
    for prop in ['location', 'rotation_euler', 'scale']:
        if o.animation_data and o.animation_data.action:o.keyframe_insert(prop, frame=216)
for key, value in morphs:
    key.value = value;key.keyframe_insert('value', frame=216)
clips = json.loads(s['kitty_clips']);clips['stir'] = [145, 216];s['kitty_clips'] = json.dumps(clips)
s.frame_set(1)
# Keep the tray level while the body leans. Heading still follows the root.
socket = bpy.data.objects['Socket_Tray']
for constraint in list(socket.constraints):
    if constraint.name == 'Level serving tray':
        socket.constraints.remove(constraint)
constraint = socket.constraints.new('COPY_ROTATION')
constraint.name = 'Level serving tray'
constraint.target = bpy.data.objects['CTRL_Root']
constraint.owner_space = 'WORLD'
constraint.target_space = 'WORLD'
# Match the tray to the small oven and preserve that authored size in the game.
bpy.data.objects['Toy_Tray'].scale = (.72, .72, .72)
preview = bpy.data.objects.get('Preview_Toy_Tray')
if preview:
    preview.scale = (.72, .72, .72)
# The oven is a real open shell, so a tray can enter its cavity instead of
# intersecting a solid enamel block behind an opening glass door.
props = bpy.data.collections['GAME — cozy props']
enamel = bpy.data.objects['Oven enamel']
enamel.dimensions = (.9, .65, .14)
enamel.location = (0, 0, .07)
for name, pos, dims in [
    ('Oven shell back', (0, .285, .44), (.9, .08, .88)),
    ('Oven shell left', (-.4, -.04, .44), (.1, .57, .74)),
    ('Oven shell right', (.4, -.04, .44), (.1, .57, .74)),
    ('Oven shell top', (0, 0, .81), (.9, .65, .14)),
]:
    o = bpy.data.objects.get(name)
    if not o:
        o = enamel.copy();o.name = name;props.objects.link(o)
    o.location = pos;o.dimensions = dims
# Match the existing paw contact to the browser's fixed oven position.
# Turn fully toward it, take a small sideways step, deposit, then withdraw.
root = bpy.data.objects['CTRL_Root']
rest = root.location.copy()
def smooth(a, b, t):
    v = max(0, min(1, (t-a)/(b-a)))
    return v*v*(3-2*v)
for f in range(511, 584, 3):
    t = (f-511)/72
    reach = smooth(.06, .68, t)*(1-smooth(.85, 1, t))
    root.location = rest + Vector((1.57*reach, -1.0*reach, 0))
    root.rotation_euler = (0, 0, math.pi/2*reach)
    root.keyframe_insert('location', frame=f)
    root.keyframe_insert('rotation_euler', frame=f)
for fc in root.animation_data.action.fcurves:
    for p in fc.keyframe_points:
        p.handle_left_type = 'AUTO_CLAMPED';p.handle_right_type = 'AUTO_CLAMPED'
# Hold the spoon by its handle and aim its scoop into the dough, instead of
# burying the scoop beneath the worktop. The paw remains the attachment point.
spoon = bpy.data.objects.get('Socket_Spoon')
if not spoon:
    spoon = bpy.data.objects.new('Socket_Spoon', None)
    bpy.data.collections['ANIMATION — select controls to pose'].objects.link(spoon)
spoon.parent = bpy.data.objects['Socket_Paw_R'];spoon.location = (0, 0, 0)
spoon.rotation_mode = 'QUATERNION'
spoon.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(Vector((.080326, -.364769, -.307962)).normalized())
spoon.scale = (1.3, 1.3, 1.3)
if bpy.data.objects.get('Preview_Toy_Spoon'):
    bpy.data.objects['Preview_Toy_Spoon'].parent = spoon
# Cutter starts above the dough and presses down to the back of the worktop.
arm = bpy.data.objects['CTRL_Arm_R']
for f in range(217, 266, 3):
    t = (f-217)/48
    press = smooth(.24, .48, t)*(1-smooth(.62, .93, t))
    anticipation = math.sin(math.pi*min(1, t/.24))*.04 if t < .24 else 0
    arm.rotation_euler = (-.2 + .25*press-anticipation if f < 265 else 0, 0, 0)
    arm.keyframe_insert('rotation_euler', frame=f)
s['Natural flow polish'] = 'Level tray constraint; oven-sized serving tray; open oven shell and aligned deposit/withdraw motion. Existing 13 clips and fused paws preserved.'
s.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().parent/'hello_kitty_natural.blend'))
print('NATURAL_FLOW_POLISHED')
