"""Author five mouthless expressions and an empty-paw rest shape in Blender.
Preserves the existing 13 contact/dance performances and fitted costume meshes.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
VERSION='expressions-v1'
FACES={'sleepy':('Sleepy',733,805),'surprised':('Surprise',805,853),'softHappy':('SoftSmile',853,925),'shy':('Shy',925,997),'curious':('Curious',997,1069)}

def ensure_key(obj,name):
 if not obj.data.shape_keys:obj.shape_key_add(name='Basis')
 return obj.data.shape_keys.key_blocks.get(name)or obj.shape_key_add(name=name)

def key_values(key,values):
 for frame,value in values:key.value=value;key.keyframe_insert('value',frame=frame)

def add_character_expressions():
 s=bpy.context.scene
 if s.get('expression_library')==VERSION:return
 s.frame_set(1);char=bpy.data.collections['HELLO KITTY — editable parts'];head=bpy.data.objects['CTRL_Head']
 for side,name in [(-1,'Eye left'),(1,'Eye right')]:
  eye=bpy.data.objects[name];world=eye.matrix_world.copy();inv=world.inverted()
  center=sum((world@v.co for v in eye.data.vertices),Vector())/len(eye.data.vertices)
  for expression,(keyname,start,end)in FACES.items():
   key=ensure_key(eye,keyname)
   for out,v in zip(key.data,eye.data.vertices):
    p=world@v.co;d=p-center;x,y,z=d
    if keyname=='Sleepy':x*=1.04;z=z*.18-.020-.024*max(0,1-(d.x/.125)**2)
    elif keyname=='Surprise':x*=1.32;z=z*1.10+.012
    elif keyname=='SoftSmile':x*=1.10;z=z*.42+.044*max(0,1-(d.x/.125)**2)
    elif keyname=='Shy':x=x*.9-side*.024;z=z*.74-.018
    else:x+=.018;z=z*(1.13 if side<0 else .82)
    out.co=inv@(center+Vector((x,y,z)))
   values=[(1,0),(727,0)]
   for _,(_,a,b)in FACES.items():values.extend([(a,0),(a+8,1 if a==start else 0),(b-10,1 if a==start else 0),(b,0)])
   values.extend([(1069,0),(1141,0)]);key_values(key,sorted(set(values)))
 # Empty hands settle lower and a little closer to the body. The shoulder root
 # remains anchored; the geometry is sculpted into an actual relative shape key.
 for side,label in [(-1,'L'),(1,'R')]:
  arm=bpy.data.objects['White arm '+str(side)];root=bpy.data.objects['CTRL_Arm_'+label].matrix_world.translation.copy()
  world=arm.matrix_world.copy();inv=world.inverted();rest=ensure_key(arm,'EmptyRest')
  rotation=Matrix.Rotation(.67,4,'X')@Matrix.Rotation(-side*.14,4,'Y')
  for out,v in zip(rest.data,arm.data.vertices):
   p=world@v.co;delta=p-root;weight=max(0,min(1,(delta.length-.14)/.22));weight=weight*weight*(3-2*weight)
   relaxed=root+rotation@delta;out.co=inv@p.lerp(relaxed,weight)
  values=[(1,0),(727,0),(733,0),(741,1),(1059,1),(1069,0),(1077,1),(1131,1),(1141,0)];key_values(rest,values)
 # Project a thin blush patch onto the actual head surface, including costumes.
 pink=bpy.data.materials.new('Expression soft blush');pink.use_nodes=True
 bs=pink.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.96,.35,.46,1);bs.inputs['Roughness'].default_value=.78;bs.inputs['Alpha'].default_value=.38
 surface=bpy.data.objects['Head'];inverse=surface.matrix_world.inverted()
 for side in [-1,1]:
  verts=[];faces=[]
  for ring in range(7):
   radius=ring/6
   for j in range(24):
    angle=j*math.tau/24;x=side*.86+.16*radius*math.cos(angle);z=3.01+.066*radius*math.sin(angle)
    hit,point,normal,_=surface.ray_cast(inverse@Vector((x,-3,z)),(inverse.to_3x3()@Vector((0,1,0))).normalized())
    p=surface.matrix_world@point if hit else Vector((x,-.84,z));n=(surface.matrix_world.to_3x3()@normal).normalized()if hit else Vector((0,-1,0));verts.append(p+n*.005)
  for ring in range(6):
   for j in range(24):a=ring*24+j;b=ring*24+(j+1)%24;faces.append((a,b,b+24,a+24))
  mesh=bpy.data.meshes.new('Curved cheek blush');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Expression blush '+str(side),mesh);char.objects.link(obj);mesh.materials.append(pink)
  obj.parent=head;obj.matrix_parent_inverse=head.matrix_world.inverted();obj['expression_detail']=True
  # The base is collapsed and the Warmth target opens the surface gently.
  basis=ensure_key(obj,'Basis');full=[v.co.copy()for v in mesh.vertices];center=sum(full,Vector())/len(full)
  for v in basis.data:v.co=center+(v.co-center)*.0001
  warmth=ensure_key(obj,'Warmth')
  for v,p in zip(warmth.data,full):v.co=p
  key_values(warmth,[(1,0),(727,0),(925,0),(935,1),(985,1),(997,0),(1141,0)])
  for p in mesh.polygons:p.use_smooth=True
 # Small authored head/paw movements support the eyes without moving the feet
 # or changing any of the established baking/socket poses.
 for name in ['CTRL_Head','CTRL_Arm_L','CTRL_Arm_R']:
  control=bpy.data.objects[name]
  for emotion,(_,start,end)in FACES.items():
   for frame,strength in [(start,0),(start+12,1),(end-16,1),(end,0)]:
    control.rotation_euler=(0,0,0)
    if name=='CTRL_Head':
     control.rotation_euler=(strength*({'sleepy':.10,'surprised':-.055,'softHappy':-.025,'shy':.07,'curious':.025}[emotion]),strength*({'shy':.10,'curious':-.13}.get(emotion,0)),0)
    control.keyframe_insert('rotation_euler',frame=frame)
  for frame in [1069,1141]:control.rotation_euler=(0,0,0);control.keyframe_insert('rotation_euler',frame=frame)
 for obj in [*char.objects,*bpy.data.collections['ANIMATION — select controls to pose'].objects]:
  data=obj.data.shape_keys if obj.type=='MESH'and obj.data.shape_keys else obj
  if data.animation_data and data.animation_data.action:
   for fc in data.animation_data.action.fcurves:
    for key in fc.keyframe_points:key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
 ranges=json.loads(s['kitty_clips']);ranges.update({name:[a,b]for name,(_,a,b)in FACES.items()});ranges['relax']=[1069,1141];s['kitty_clips']=json.dumps(ranges)
 for obj in char.objects:
  ancestor=obj
  while ancestor and ancestor.name!='CTRL_Bouquet':ancestor=ancestor.parent
  if ancestor:obj.hide_render=True;obj.hide_viewport=True
 s['expression_library']=VERSION;s['default_empty_frame']=1105;s['expression_guide']='Face shapes: Sleepy, Surprise, SoftSmile, Shy, Curious; projected Warmth blush; EmptyRest paw shape. Existing clips 1–727 preserved. New expressions 733–1069, relaxed empty-paw pose 1069–1141. Optional bouquet hidden by default.'
 s.frame_end=1141;s.frame_set(1105);print('BLENDER_EXPRESSIONS_READY',s.get('plush_variant','classic'),flush=True)

if __name__=='__main__':
 add_character_expressions();s=bpy.context.scene;style=s.get('plush_variant','classic');draft='--draft'in sys.argv
 path=Path('/tmp')/('expression-'+style+'.blend')if draft else Path(bpy.data.filepath)
 s.render.filepath='//hello_kitty_plush_'+style+'.png' if style!='classic' else '//hello_kitty_natural.png'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if '--portrait' in sys.argv:bpy.ops.render.render(write_still=True)
 if '--render'in sys.argv:
  for label,frame in [('rest',1105),('sleepy',765),('surprised',829),('softHappy',885),('shy',961),('curious',1033)]:
   s.frame_set(frame);s.render.filepath='/tmp/kitty-expression-'+style+'-'+label+'.png';bpy.ops.render.render(write_still=True)
