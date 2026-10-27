"""Add a reversible, editable object-control rig and 6-second animation.
Run after create_hello_kitty.py: blender -b hello_kitty.blend --python-exit-code 1 --python animate_hello_kitty.py
Add -- --render to render the PNG sequence into animation_frames/.
"""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Matrix
OUT = Path(__file__).resolve().parent
s = bpy.context.scene
if bpy.data.objects.get('CTRL_Root'):
    raise RuntimeError('Already animated. Start from the static hello_kitty.blend.')
coll=bpy.data.collections.new('ANIMATION — select controls to pose')
s.collection.children.link(coll)

def control(name,loc,parent=None):
    o=bpy.data.objects.new(name,None)
    coll.objects.link(o)
    o.empty_display_type='CIRCLE'
    o.empty_display_size=.3
    o.location=loc
    if parent:
        keep=Matrix.Translation(loc)
        o.parent=parent
        bpy.context.view_layer.update()
        o.matrix_world=keep
    return o

def attach(o,parent):
    world=o.matrix_world.copy()
    o.parent=parent
    o.matrix_world=world

root=control('CTRL_Root',(0,0,.43))
body=control('CTRL_Body',(0,0,1.4),root)
head=control('CTRL_Head',(0,0,2.5),body)
flower=control('CTRL_Bouquet',(0,-1.1,1.9),body)
arms={i:control('CTRL_Arm_'+('L' if i<0 else 'R'),(i*.76,-.35,2.1),body) for i in [-1,1]}
feet={i:control('CTRL_Foot_'+('L' if i<0 else 'R'),(i*.44,0,.72),root) for i in [-1,1]}
bpy.context.view_layer.update()
for o in list(bpy.data.collections['HELLO KITTY — editable parts'].objects):
    n=o.name
    if n=='Head' or n.startswith(('Eye','Whisker','Yellow oval nose','Bow')):
        dest=head
    elif n.startswith(('Pink daisy','Yellow daisy','Pink flower','Yellow flower','Bouquet leaf','Leaf vein')):
        dest=flower
    elif n.startswith(('White arm','Mitten hand','Thumb')):
        dest=arms[-1 if n.endswith('-1') else 1]
    elif n.startswith('Foot'):
        dest=feet[-1 if n.endswith('-1') else 1]
    else:
        dest=body
    attach(o,dest)

# Closed-eye arc replaces the open oval for a wink.
open_eye=bpy.data.objects['Eye right']
data=bpy.data.curves.new('Closed wink arc','CURVE')
data.dimensions='3D'; data.bevel_depth=.025; data.bevel_resolution=4
sp=data.splines.new('BEZIER'); sp.bezier_points.add(2)
for p,co in zip(sp.bezier_points,[(.52,-.972,3.27),(.63,-.993,3.32),(.74,-.972,3.27)]):
    p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
wink=bpy.data.objects.new('Wink — closed eye',data)
bpy.data.collections['HELLO KITTY — editable parts'].objects.link(wink)
data.materials.append(bpy.data.materials['Eyes and whiskers'])
attach(wink,head)
for f,closed in [(1,False),(78,False),(79,True),(87,True),(88,False),(144,False)]:
    open_eye.hide_render=closed; open_eye.hide_viewport=closed
    wink.hide_render=not closed; wink.hide_viewport=not closed
    for o in [open_eye,wink]:
        o.keyframe_insert('hide_render',frame=f); o.keyframe_insert('hide_viewport',frame=f)

s.frame_start=1; s.frame_end=144; s.render.fps=24
base={o:o.location.copy() for o in [root,body,head,flower,*arms.values(),*feet.values()]}
def key(o,f,offset=(0,0,0),rot=(0,0,0),scale=(1,1,1)):
    o.location=base[o]+__import__('mathutils').Vector(offset)
    o.rotation_euler=rot; o.scale=scale
    for prop in ['location','rotation_euler','scale']:
        o.keyframe_insert(prop,frame=f)

# Repeated, gentle bounce with side-to-side dance turns; rest pose loops cleanly.
for f in range(1,146,12):
    t=(f-1)/12
    lift=.14 if int(t)%2 else 0
    sway=math.sin(t*math.pi/2)
    key(root,min(f,144),(.055*sway,0,lift),(0,.045*sway,.10*sway))
    key(body,min(f,144),rot=(0,-.045*sway,0),scale=(1.015,1.015,.985) if lift==0 and f not in [1,145] else (1,1,1))
    for i,o in feet.items():
        key(o,min(f,144),rot=(0,i*.09*max(0,sway*i),0))
key(root,144);key(body,144)
for o in feet.values(): key(o,144)
for f,tilt in [(1,0),(24,-.07),(48,.07),(66,-.11),(82,-.14),(96,0),(116,.10),(132,0),(144,0)]:
    key(head,f,rot=(0,tilt,0))
# Wave, then bring both hands forward with the bouquet.
for i,o in arms.items():
    key(o,1);key(o,48)
    if i<0:
        for f,a in [(60,2.35),(66,2.65),(72,2.30),(78,2.65),(84,2.35)]:
            key(o,f,(-.12,0,.35),(0,a,0))
    key(o,96)
    key(o,112,(0,-.27,.12),(-.12,0,0)); key(o,124,(0,-.27,.12),(-.12,0,0))
    key(o,138);key(o,144)
for f,off in [(1,(0,0,0)),(96,(0,0,0)),(112,(0,-.27,.12)),(124,(0,-.27,.12)),(138,(0,0,0)),(144,(0,0,0))]:
    key(flower,f,off)
for name,f in [('Bounce',1),('Dance',25),('Wave',60),('Wink',79),('Offer flowers',112),('Loop end',144)]:
    s.timeline_markers.new(name,frame=f)
# Eevee produces clean animation without Cycles grain, on supported graphics drivers.
s.render.engine='BLENDER_EEVEE_NEXT'
s.eevee.taa_render_samples=32
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'animation_frames'/'frame_')
s['Animation help']='Space: play frames 1–144 (24 fps). Select CTRL_* empties to pose. Object-control toy rig; not a deforming skeletal rig. Markers identify gestures. Static source remains hello_kitty.blend.'
s.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hello_kitty_animated.blend'))
assert all(o.animation_data and o.animation_data.action for o in [root,body,head,flower,*arms.values(),*feet.values()])
assert head.parent==body and body.parent==root
s.frame_set(82);assert wink.hide_render==False and open_eye.hide_render==True
s.frame_set(1);assert wink.hide_render and not open_eye.hide_render
print('ANIMATION_VALIDATED: hierarchy, keyed controls, wink and loop timeline')
if '--preview' in sys.argv:
    s.render.resolution_x=400; s.render.resolution_y=400
    s.eevee.taa_render_samples=8
    s.frame_step=2
if '--render' in sys.argv:
    (OUT/'animation_frames').mkdir(exist_ok=True)
    bpy.ops.render.render(animation=True)
