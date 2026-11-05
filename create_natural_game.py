"""Natural, input-driven toy performances. Preserves hello_kitty_game.blend.
blender -b hello_kitty_game.blend --python-exit-code 1 --python create_natural_game.py
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
ctrl=bpy.data.collections['ANIMATION — select controls to pose']
names=['CTRL_Root','CTRL_Body','CTRL_Head','CTRL_Arm_L','CTRL_Arm_R','CTRL_Foot_L','CTRL_Foot_R','CTRL_Bouquet']
base={n:bpy.data.objects[n].location.copy() for n in names}
clips=json.loads(s['kitty_clips']);clips.update(placeTray=[511,583],sprinkle=[583,655],handoff=[655,727])
def smooth(a,b,t):
 v=max(0,min(1,(t-a)/(b-a)));return v*v*(3-2*v)
def key(n,f,rot=(0,0,0),offset=(0,0,0)):
 o=bpy.data.objects[n];o.location=base[n]+Vector(offset);o.rotation_euler=rot;o.scale=(1,1,1)
 for p in ['location','rotation_euler','scale']:o.keyframe_insert(p,frame=f)
# Deform the actual fused arm mesh with a smooth shoulder-to-paw falloff.
# Mesh reduction happens BEFORE morph creation; subsequent exports preserve keys.
arm_data={}
for side,sign in [('L',-1),('R',1)]:
 o=bpy.data.objects['White arm '+str(sign)];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):o.modifiers.remove(m)
 d=o.modifiers.new('Portable smooth arm topology','DECIMATE');d.ratio=.35;bpy.ops.object.modifier_apply(modifier=d.name)
 o.shape_key_add(name='Basis');curl=o.shape_key_add(name='Elbow_soft');soft=o.shape_key_add(name='Paw_soft')
 world=o.matrix_world.copy();inv=world.inverted();elbow=Vector((sign*.76,-.63,1.85))
 def deform(p,amount,axis='X'):
  weight=smooth(-.48,-.92,p.y) if False else smooth(.05,.48,-p.y-.39)
  return p.lerp(elbow+Matrix.Rotation(amount,4,axis)@(p-elbow),weight)
 for i,v in enumerate(o.data.vertices):
  p=world@v.co;curl.data[i].co=inv@deform(p,-.26);soft.data[i].co=inv@deform(p,sign*.10,'Z')
 socket=bpy.data.objects['Socket_Paw_'+side];rest=socket.location.copy();rest_world=socket.matrix_world.translation.copy();parent_inv=socket.parent.matrix_world.inverted().to_3x3()
 arm_data[side]=(curl,soft,socket,rest,parent_inv@(deform(rest_world,-.26)-rest_world),parent_inv@(deform(rest_world,sign*.10,'Z')-rest_world))
 for k in [curl,soft]:k.value=0;k.keyframe_insert('value',frame=1);k.keyframe_insert('value',frame=144)
for name in ['stir','cut','present','surprise','bow','celebrate','sip','placeTray','sprinkle','handoff']:
 start,end=clips[name]
 for f in range(start,end+1,3):
  t=(f-start)/(end-start);engage=smooth(0,.19,t)*(1-smooth(.80,1,t));settle=math.sin(t*math.pi)**2
  for n in names:key(n,f)
  bend={'L':0,'R':0};grip={'L':0,'R':0}
  if name=='stir':
   # A loopable contact pose; the hand traces the bowl, the elbow yields gently.
   a=t*math.tau;key('CTRL_Arm_R',f,(-.65+.10*math.cos(a),.10*math.sin(a),-.035));key('CTRL_Arm_L',f,(.03,0,0));key('CTRL_Head',f,(.10,-.04,0));bend['R']=.20+.12*math.sin(a);grip['R']=.35
  elif name=='cut':
   press=smooth(.24,.48,t)*(1-smooth(.62,.93,t));anticipation=math.sin(math.pi*min(1,t/.24))*.06 if t<.24 else 0
   key('CTRL_Arm_R',f,(.29*press-anticipation,0,0));key('CTRL_Head',f,(.10*engage,0,0));key('CTRL_Body',f,(.025*press,0,0));bend['R']=.25*press;grip['R']=.3*engage
  elif name in ['present','handoff']:
   p=(.85+.2*math.sin(math.pi*min(1,t/.7)))*(1-smooth(.7,1,t)) if name=='handoff' else engage
   for side in ['L','R']:key('CTRL_Arm_'+side,f,(-.38*p,0,0));bend[side]=.3*p;grip[side]=.4*p
   key('CTRL_Head',f,(.04*p,-.055*p,0));key('CTRL_Body',f,(.035*p,0,0))
  elif name=='placeTray':
   reach=smooth(.06,.68,t)*(1-smooth(.85,1,t))
   key('CTRL_Root',f,(0,0,.85*reach),(.60*reach,0,0))
   key('CTRL_Body',f,(.09*reach,0,0));key('CTRL_Head',f,(.08*reach,0,0))
   for side in ['L','R']:key('CTRL_Arm_'+side,f,(.18*reach,0,0));bend[side]=.2*reach;grip[side]=.3*reach
   key('CTRL_Foot_L',f,offset=(0,0,math.sin(math.pi*smooth(.04,.34,t))*.05 if t<.34 else 0))
   key('CTRL_Foot_R',f,offset=(0,0,math.sin(math.pi*smooth(.22,.51,t))*.035 if .22<t<.51 else 0))
  elif name=='sprinkle':
   key('CTRL_Arm_R',f,(-.22*engage,.07*math.sin(t*math.tau*2)*engage,0));key('CTRL_Head',f,(.07*engage,0,0));bend['R']=.45*engage;grip['R']=.5*engage
  elif name=='surprise':key('CTRL_Head',f,(-.07*engage,-.12*engage,0),offset=(0,0,.025*engage))
  elif name=='bow':key('CTRL_Body',f,(.11*engage,0,0));key('CTRL_Head',f,(.09*engage,0,0))
  elif name=='celebrate':
   lift=(1-math.cos(t*math.tau*2))*.025*engage;key('CTRL_Root',f,offset=(0,0,lift))
   for side,sign in [('L',-1),('R',1)]:key('CTRL_Arm_'+side,f,(0,sign*.55*engage,0));bend[side]=.25*engage
   key('CTRL_Head',f,(0,.05*math.sin(t*math.tau)*engage,0))
  elif name=='sip':key('CTRL_Arm_R',f,(-.85*engage,0,0));key('CTRL_Head',f,(.06*engage,0,0));bend['R']=.3*engage;grip['R']=.35*engage
  for side,(curl,soft,socket,rest,dc,ds) in arm_data.items():
   curl.value=bend[side];soft.value=grip[side];curl.keyframe_insert('value',frame=f);soft.keyframe_insert('value',frame=f)
   socket.location=rest+dc*curl.value+ds*soft.value;socket.keyframe_insert('location',frame=f)
 for o in ctrl.objects:
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    for p in fc.keyframe_points:p.handle_left_type='AUTO_CLAMPED';p.handle_right_type='AUTO_CLAMPED'
 s.timeline_markers.new('Natural '+name,frame=start)
# Openable oven door, with its pivot at the bottom hinge.
props=bpy.data.collections['GAME — cozy props'];oven=bpy.data.objects['Toy_Oven'];bpy.context.view_layer.update()
hinge=bpy.data.objects.new('Oven_Door',None);props.objects.link(hinge);hinge.parent=oven;hinge.location=(0,-.36,.15);bpy.context.view_layer.update()
for name in ['Oven window','Oven glass','Oven handle']:
 o=bpy.data.objects[name];m=o.matrix_world.copy();o.parent=hinge;o.matrix_world=m
# A rounded parcel and a small flower pot share the existing toy palette.
rose=bpy.data.materials['Game rose porcelain'];cream=bpy.data.materials['Game warm cream'];mint=bpy.data.materials.get('Game sage') or bpy.data.materials.new('Game sage');mint.diffuse_color=(.46,.64,.48,1)
def root(name):
 o=bpy.data.objects.new(name,None);props.objects.link(o);return o
sphere_cache={}
def mesh(parent,name,pos,scale,material,cube=False):
 if cube:bpy.ops.mesh.primitive_cube_add(size=1)
 else:bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10)
 o=bpy.context.object;o.name=name
 if not cube:
  if material.name in sphere_cache:
   old=o.data;o.data=sphere_cache[material.name];bpy.data.meshes.remove(old)
  else:sphere_cache[material.name]=o.data
 for c in list(o.users_collection):c.objects.unlink(o)
 props.objects.link(o);o.parent=parent;o.location=pos;o.scale=scale
 if not o.data.materials:o.data.materials.append(material)
 if cube:
  bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);mod=o.modifiers.new('Rounded paper edges','BEVEL');mod.width=.06;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 return o
r=root('Toy_Parcel');mesh(r,'Cookie parcel',(0,0,.03),(.95,.53,.22),cream,True);mesh(r,'Parcel ribbon',(0,-.275,.05),(.12,.025,.23),rose,True);r.location=(8,0,0)
r=root('Toy_Flowers');mesh(r,'Flower pot',(0,0,.14),(.2,.18,.17),rose)
for i in range(3):
 x=(i-1)*.18;z=.55+(i%2)*.10;mesh(r,'Flower stem',(x,0,.34),(.018,.018,.27),mint)
 for j in range(5):
  a=j*math.tau/5;mesh(r,'Flower petal',(x+math.cos(a)*.09,-.02,z+math.sin(a)*.09),(.085,.045,.09),cream)
 mesh(r,'Flower heart',(x,-.07,z),(.055,.035,.055),rose)
r.location=(10,0,0)
# Crescent cutter matches the discoverable moon recipe.
r=root('Toy_Cutter_Moon');points=[]
for i in range(41):
 a=math.pi/3+(4*math.pi/3)*i/40;points.append((.20*math.cos(a),.20*math.sin(a)))
for i in range(1,31):
 a=math.pi*1.5-math.pi*i/30;points.append((.1+.173205*math.cos(a),.173205*math.sin(a)))
n=len(points);verts=[]
for z,factor in [(-.025,1),(-.025,.91),(.025,1),(.025,.91)]:verts.extend((x*factor,y*factor,z) for x,y in points)
faces=[]
for i in range(n):
 j=(i+1)%n;faces.extend([(i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)])
data=bpy.data.meshes.new('Moon cutter rim');data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new('Moon cutter',data);props.objects.link(o);o.parent=r;data.materials.append(rose);r.location=(12,0,0)
s['kitty_clips']=json.dumps(clips);s.frame_end=727;s.render.filepath='//natural_frames/frame_';s['Animation help']='Natural game edition: 24fps, named clips, soft elbow/paw shape keys and synced paw sockets. Original source files preserved.';s.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().parent/'hello_kitty_natural.blend'))
print('NATURAL_MOTIONS_READY',len(clips),'clips, smooth elbow morphs, synchronized grips, oven hinge and new props')
