"""Create separate editable home-performance projects; originals stay intact.
blender -b hello_kitty_natural.blend --python-exit-code 1 --python author_home_motions.py
Exports lightweight controller-only clips, sharing the original character rig.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
s=bpy.context.scene;original=Path(bpy.data.filepath);style=s.get('plush_variant','classic')
s.frame_set(s.get('default_empty_frame',1105));bpy.context.view_layer.update()
controls=list(bpy.data.collections['ANIMATION — select controls to pose'].objects)
controls=[o for o in controls if o.type=='EMPTY']
base={o.name:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy())for o in controls}
foot=bpy.data.objects['Foot -1'];floor=min((foot.matrix_world@Vector(c)).z for c in foot.bound_box)
height=s.get('plush_body_height',4.56808);norm=2.27/height;web_scale=.9
body=bpy.data.objects['Strawberry pink rounded dress'];bottom=min((body.matrix_world@Vector(c)).z for c in body.bound_box)
# Settle the stuffed body slightly into the real chair cushion, leaving toes free.
rise=(.775-.145-.025-(bottom-floor)*norm*web_scale)/(norm*web_scale)
for o in controls:o.animation_data_clear()
for o in bpy.data.collections['HELLO KITTY — editable parts'].objects:
 o.animation_data_clear()
 ancestor=o
 while ancestor and ancestor.name!='CTRL_Bouquet':ancestor=ancestor.parent
 if ancestor or 'Wink' in o.name or 'happy left eye' in o.name:o.hide_render=True;o.hide_viewport=True
 if o.data and hasattr(o.data,'shape_keys') and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for key in o.data.shape_keys.key_blocks:
   if key.name!='Basis':key.value=1 if key.name=='EmptyRest'else 0
# All performances share exactly the same seated endpoint.
ranges={'sitDown':[1,37],'sitIdle':[37,133],'takeCup':[133,157],'sipSit':[157,205],'putCup':[205,229],'standUp':[229,265],'cupIdle':[277,373]}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for name,(start,end)in ranges.items():
 for frame in range(start,end+1):
  s.frame_set(frame);t=(frame-start)/(end-start)
  for o in controls:o.location=base[o.name][0];o.rotation_euler=base[o.name][1];o.scale=base[o.name][2]
  seat=smooth(t)if name=='sitDown'else 1-smooth(t)if name=='standUp'else 1
  root=bpy.data.objects['CTRL_Root'];root.location.z+=rise*seat
  if name in ['sitDown','standUp']:root.location.z+=.13*math.sin(math.pi*t)**2
  bodyctrl=bpy.data.objects['CTRL_Body'];bodyctrl.rotation_euler.x=(.12*math.sin(math.pi*t)**2 if name in ['sitDown','standUp']else .012*math.sin(math.tau*t) if name=='sitIdle'else 0)
  head=bpy.data.objects['CTRL_Head'];head.rotation_euler.y=.025*math.sin(math.tau*t) if name=='sitIdle'else 0
  for side in ['L','R']:
   f=bpy.data.objects['CTRL_Foot_'+side];f.location.y-=.62*seat;f.rotation_euler.x=.20*seat
  arm=bpy.data.objects['CTRL_Arm_R']
  if name=='takeCup':arm.rotation_euler.x=.10*math.sin(math.pi*t)**2-.22*smooth(max(0,(t-.4)/.6))
  elif name=='cupIdle':arm.rotation_euler.x=-.22
  elif name=='sipSit':arm.rotation_euler.x=-.22-.65*math.sin(math.pi*t)**2;head.rotation_euler.x=.045*math.sin(math.pi*t)**2
  elif name=='putCup':arm.rotation_euler.x=-.22*(1-smooth(t))+.10*math.sin(math.pi*t)**2
  for o in controls:
   for prop in ['location','rotation_euler','scale']:o.keyframe_insert(prop,frame=frame)
for o in controls:
 if o.animation_data and o.animation_data.action:
  for f in o.animation_data.action.fcurves:
   for k in f.keyframe_points:k.interpolation='LINEAR'
s['home_motion_library']='cozy-home-v1';s['home_original_source']=original.name;s['home_original_sha256']=hashlib.sha256(original.read_bytes()).hexdigest();s['home_clips']=json.dumps(ranges)
s['home_motion_guide']='24fps home poses: hop gently onto a chair, seated breathing, reach for a cup, sip, replace it, hop down. Original character and all previous animations remain in their separate source files. This project carries only home performances.'
s.frame_start=1;s.frame_end=373;s.frame_set(61);bpy.context.view_layer.update()
# Cup rest location is derived from the actual seated grip, for matching placement.
p=bpy.data.objects['Socket_Teacup'].matrix_world.translation
cup=[p.x*norm*web_scale,(p.z-floor)*norm*web_scale+.145,-p.y*norm*web_scale]
# An editable preview chair makes the seated pose understandable in Blender.
preview=bpy.data.collections.new('HOME — preview chair (not exported)');s.collection.children.link(preview)
material=bpy.data.materials.get('Game warm cream')or body.data.materials[0]
def chair_box(name,position,size):
 bpy.ops.mesh.primitive_cube_add(size=1,location=position);o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 preview.objects.link(o);o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 bevel=o.modifiers.new('Soft chair edge','BEVEL');bevel.width=.07;bevel.segments=3
 return o
unit=norm*web_scale;top=floor+(.775-.145)/unit
chair_box('Home preview seat',(0,0,top-.075/unit),(1.08/unit,1/unit,.15/unit))
chair_box('Home preview back',(0,.48/unit,floor+(1.13-.145)/unit),(1.12/unit,.12/unit,.92/unit))
for x in [-.4,.4]:
 for y in [-.36,.36]:chair_box('Home preview leg',(x/unit,y/unit,(floor+top-.15/unit)/2),(.06/unit,.06/unit,top-.15/unit-floor))
# Preview framing uses the actual edition silhouette, including tall costumes.
points=[o.matrix_world@Vector(c)for o in bpy.data.collections['HELLO KITTY — editable parts'].objects if o.type=='MESH' and not o.hide_render for c in o.bound_box]
lo=min(v.z for v in points);hi=max(v.z for v in points);target=Vector((0,0,(lo+hi)/2))
if s.camera:
 s.camera.location=target+Vector((7,-12,5));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=(hi-lo)*1.32
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=64;s.render.resolution_x=720;s.render.resolution_y=900;s.render.resolution_percentage=100
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
folder=ROOT/'home_motions';folder.mkdir(exist_ok=True);blend=folder/f'kitty_home_{style}.blend'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
import runpy
runpy.run_path(str(ROOT/'export_home_motions.py'),run_name='__main__')
