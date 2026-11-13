"""Append editable, grounded partner gestures to a NEW character source.

blender -b hello_kitty_natural.blend --python-exit-code 1 --python author_together_motions.py
blender -b friends/melody.blend --python-exit-code 1 --python author_together_motions.py
Original geometry, expressions, actions and saved empty-paw pose are retained.
"""
import bpy, math, json, hashlib, runpy
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
s = bpy.context.scene
original = Path(bpy.data.filepath)
melody = s.get('friend_character') == 'melody'
style = 'melody' if melody else s.get('plush_variant', 'classic')
rig = bpy.data.collections['CONTROLS — pose these' if melody else 'ANIMATION — select controls to pose']
controls = [o for o in rig.objects if o.type == 'EMPTY']
rest_frame = 1 if melody else 1105
s.frame_set(rest_frame); bpy.context.view_layer.update()
base = {o.name: (o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for o in controls}
norm = 2.27 / (3.15422 if melody else s.get('plush_body_height', 4.56808))
unit = norm * .78
feet = [bpy.data.objects[n] for n in (['Foot L', 'Foot R'] if melody else ['Foot -1', 'Foot 1']) if n in bpy.data.objects]
if not feet:
    feet = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent and o.parent.name.startswith('CTRL_Foot')]
floor = min((o.matrix_world @ Vector(c)).z for o in feet for c in o.bound_box)
names = ['togetherWave', 'togetherHighfiveL', 'togetherHighfiveR', 'togetherCelebrate', 'togetherStir', 'togetherDecorate', 'togetherPresent']
ranges = {name: [1501 + i*108, 1501 + i*108 + (96 if name in ['togetherStir', 'togetherDecorate'] else 72)] for i,name in enumerate(names)}

def smooth(t):
    t = max(0., min(1., t)); return t*t*(3-2*t)

def envelope(t):
    # Anticipation 0-.125, deliberate lift .125-.333, contact .333-.417,
    # soft recovery .417-.875, then a settled empty-paw rest.
    return smooth((t-.125)/(.333333-.125)) * (1-smooth((t-.416667)/(.875-.416667)))

def web(p): return [p.x*unit, (p.z-floor)*unit, -p.y*unit]
def unweb(p): return Vector((p[0]/unit, -p[2]/unit, p[1]/unit+floor))
def y_up(v): return [v.x, v.z, -v.y]

# Surface points come from the actual relaxed mesh's rounded distal cap.
# They are separate from the legacy occupied-hand grip sockets.
tip = {}; sockets = {}; targets = {}; contact_metadata = {}; shoulder_reach = {}
for side,sign in [('L',-1),('R',1)]:
    arm = bpy.data.objects['CTRL_Arm_'+side]
    mesh = bpy.data.objects['Relaxed paw '+side if melody else ('White arm -1' if side == 'L' else 'White arm 1')]
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    vertices = [evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
    bottom = min(v.z for v in vertices)
    cap = [v for v in vertices if v.z < bottom + (.025 if melody else .035)]
    p = sum(cap, Vector())/len(cap)
    tip[side] = arm.matrix_world.inverted() @ p
    socket = bpy.data.objects.new('Together_Palm_'+side, None); rig.objects.link(socket)
    socket.parent = arm; socket.location = tip[side]; socket.empty_display_size = .07
    socket['purpose'] = 'Actual relaxed paw distal surface; occupied grips use Together_Grip_'+side
    sockets[side] = socket
    shoulder = arm.matrix_world.translation
    target_height = .72
    target_x = sign*.25
    z = target_height/unit + floor
    x = target_x/unit
    extended_tip = tip[side].copy(); extended_tip.z *= 1.14
    radius = extended_tip.length
    reach2 = radius*radius - (x-shoulder.x)**2 - (z-shoulder.z)**2
    if reach2 <= 0: raise RuntimeError('Contact outside natural paw reach: '+style+side)
    # Short plush paws reach from a gently protracted shoulder. Their upper
    # rounded caps stay embedded in the original torso. A small longitudinal
    # extension represents the curved relaxed elbow straightening; width is
    # retained. Both roles share a .84-world spacing, including neutral frames.
    forward = .38 if melody else .46
    natural_forward = -(shoulder.y-math.sqrt(reach2))*unit
    shoulder_reach[side] = (forward-natural_forward)/unit
    target = Vector((x, -forward/unit, z))
    targets[side] = target
    contact_metadata[side] = {'control':arm.name,'socket':socket.name,'socket_local_y_up':y_up(tip[side]),'contact_actor_local':web(target),'shoulder_actor_local':web(shoulder),'surface_radius_actor':radius*unit}
    grip = bpy.data.objects.new('Together_Grip_'+side, None); rig.objects.link(grip); grip.parent = arm
    if not melody:
        legacy=bpy.data.objects['Socket_Paw_'+side]
        grip.location = arm.matrix_world.inverted() @ legacy.matrix_world.translation
    else:
        # Rounded front/distal portion of Melody's existing paw, no fingers.
        grip.location = (sign*.08,-.12,-.38)
    grip.empty_display_size = .06
controls += [o for o in rig.objects if o.type=='EMPTY' and o.name.startswith('Together_')]
for o in controls:
    if o.name not in base: base[o.name]=(o.location.copy(),o.rotation_euler.copy(),o.scale.copy())

def aim(side, target, amount=1.):
    arm=bpy.data.objects['CTRL_Arm_'+side]
    bpy.context.view_layer.update()
    local = arm.parent.matrix_world.inverted() @ target - arm.location
    scaled_tip = Vector(tuple(tip[side][i]*arm.scale[i] for i in range(3)))
    rotation = scaled_tip.rotation_difference(local)
    arm.rotation_euler = Quaternion().slerp(rotation, amount).to_euler('XYZ')

shape_meshes = [o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys]
rest_shapes = {o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.name!='Basis'} for o in shape_meshes}
for name,(first,last) in ranges.items():
    s.timeline_markers.new(name, frame=first)
    for frame in range(first,last+1):
        s.frame_set(frame); t=(frame-first)/(last-first); e=envelope(t)
        for o in controls: o.location=base[o.name][0]; o.rotation_euler=base[o.name][1]; o.scale=base[o.name][2]
        body=bpy.data.objects['CTRL_Body']; head=bpy.data.objects['CTRL_Head']
        # Feet and root remain at their original ground transforms throughout.
        body.rotation_euler.x = -.025*math.sin(math.pi*t)**2
        head.rotation_euler.y = .045*math.sin(math.pi*t)**2
        anticipation = -.13*math.sin(math.pi*min(1,t/.125))**2 if t<.125 else 0
        for side,sign in [('L',-1),('R',1)]:
            arm=bpy.data.objects['CTRL_Arm_'+side]
            arm.rotation_euler.x=anticipation
        if name.startswith('togetherHighfive'):
            side=name[-1]
            bpy.data.objects['CTRL_Arm_'+side].location.y -= shoulder_reach[side]*e
            bpy.data.objects['CTRL_Arm_'+side].scale.z = 1+.14*e
            if melody:
                # The rounded upper cap transfers from torso to lower hood
                # as the paw rises; a tiny shoulder lift keeps it connected.
                bpy.data.objects['CTRL_Arm_'+side].location.z += .08*math.sin(math.pi*e)
            # Exact shoulder-driven arc, same measured surface point throughout.
            aim(side,targets[side],e)
            head.rotation_euler.z = (-.045 if side=='L' else .045)*e
            if e>.99999: body.rotation_euler.x=0; head.rotation_euler.y=0; aim(side,targets[side],1)
            head.rotation_euler.x = -.035*e
        elif name=='togetherWave':
            side='R'; shoulder=bpy.data.objects['CTRL_Arm_R'].matrix_world.translation
            target=shoulder+Vector((.24,-.25,.5))*(1 if melody else 1.3)
            aim(side,target,e)
            bpy.data.objects['CTRL_Arm_R'].rotation_euler.y += .19*math.sin(t*math.tau*3)*e
            head.rotation_euler.z = -.045*e
        elif name=='togetherCelebrate':
            for side,sign in [('L',-1),('R',1)]:
                shoulder=bpy.data.objects['CTRL_Arm_'+side].matrix_world.translation
                aim(side,shoulder+Vector((sign*.35,-.20,.55)),e)
            head.rotation_euler.x=-.05*e
        else:
            # Prop motions use the original occupied Kitty grip geometry.
            # Melody's same real rounded paw cups the tool at the explicit grip.
            for side,sign in [('L',-1),('R',1)]:
                arm=bpy.data.objects['CTRL_Arm_'+side]
                if melody:
                    arm.rotation_euler.x = -1.02*e
                    arm.rotation_euler.y = -sign*.16*e
                else:
                    arm.rotation_euler.x = -.18*e
                    arm.rotation_euler.y = -sign*.08*e
            right=bpy.data.objects['CTRL_Arm_R']
            if name=='togetherStir':
                right.rotation_euler.x += .12*math.cos(t*math.tau*2)*e
                right.rotation_euler.y += .14*math.sin(t*math.tau*2)*e
                head.rotation_euler.x=.055*e
            elif name=='togetherDecorate':
                right.rotation_euler.x += .105*math.sin(t*math.tau*3)*e
                right.rotation_euler.z += .08*math.sin(t*math.tau*1.5)*e
                head.rotation_euler.x=.06*e
            else:
                for side in ['L','R']: bpy.data.objects['CTRL_Arm_'+side].rotation_euler.x -= .16*e
                head.rotation_euler.x=.045*e
        for o in controls:
            for prop in ['location','rotation_euler','scale']: o.keyframe_insert(prop,frame=frame)
        for o in shape_meshes:
            keys=o.data.shape_keys.key_blocks
            for key in keys:
                if key.name=='Basis': continue
                key.value=rest_shapes[o.name][key.name]
                if key.name=='EmptyRest' and name in ['togetherStir','togetherDecorate','togetherPresent']: key.value=1-e
                if key.name in ['SoftSmile','Warmth']: key.value=.35*e
                key.keyframe_insert('value',frame=frame)
    print('AUTHORED_TOGETHER',style,name,flush=True)

# Preserve the old key interpolation; only the appended samples are linear.
for o in controls:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                if k.co.x>=1501:k.interpolation='LINEAR'
s['together_library']='together-v1';s['together_clips']=json.dumps(ranges)
s['together_original_source']=str(original.relative_to(ROOT));s['together_original_sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
s['together_style']=style;s['together_norm']=norm;s['together_floor']=floor
s['together_contact']=json.dumps(contact_metadata)
s['together_rest_offsets']=json.dumps({o.name:y_up(base[o.name][0]) for o in controls})
s['together_guide']='Seven additive partner clips; originals preserved before frame 1501. 24fps. Highfive contact at +24, held through +30; feet grounded. Together_Palm_L/R are actual relaxed surface points, Together_Grip_L/R hold tools. Runtime must subtract existing additive-pivot bind translations and switch Kitty EmptyRest to 0 for occupied props.'
folder=ROOT/'together_motions';folder.mkdir(exist_ok=True)
s.frame_start=1;s.frame_end=max(last for first,last in ranges.values());s.frame_set(rest_frame)
bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(folder/('together_'+style+'.blend')),compress=True)
runpy.run_path(str(ROOT/'export_together_motions.py'),run_name='__main__')
