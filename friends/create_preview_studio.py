"""Render actual Blender models in a shared studio and illustrated pose sheets."""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import create_friends as lib
bpy.ops.wm.read_factory_settings(use_empty=False);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):bpy.data.collections.remove(col)
stage=bpy.data.collections.new('STUDIO — three little friends');bpy.context.scene.collection.children.link(stage)
characters=[]
for style,x in [('kuromi',-3.1),('melody',0),('cinnamoroll',3.1)]:
 with bpy.data.libraries.load(str(HERE/(style+'.blend')))as(src,dst):dst.collections=['CHARACTER — '+lib.TITLES[style],'CONTROLS — pose these']
 char,rig=dst.collections
 for col in [char,rig]:bpy.context.scene.collection.children.link(col)
 holder=bpy.data.objects.new('Friend — '+lib.TITLES[style],None);stage.objects.link(holder);holder.location.x=x
 root=next(o for o in rig.objects if o.name.startswith('CTRL_Root'));root.parent=holder
 characters.append((style,x,char,rig,holder))
lib.stage=stage;lib.style='melody';lib.studio();s=bpy.context.scene;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.fps=24;s.frame_start=1;s.frame_end=1441
bpy.data.objects.remove(bpy.data.objects['Studio plinth'],do_unlink=True)
base=bpy.data.materials['Studio biscuit']
for _,x,_,_,_ in characters:
 bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=1.35,depth=.10,location=(x,0,-.04));o=lib.link(bpy.context.object,stage);o.data.materials.append(base);m=o.modifiers.new('Soft plinth edge','BEVEL');m.width=.045;m.segments=3
for name,mult in [('Large warm key',2),('Soft cream fill',2),('Pink rim',2)]:bpy.data.objects[name].data.energy*=mult;bpy.data.objects[name].data.size*=1.4
cam=s.camera;cam.location=(5,-15,6.0);cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=10.2
s['friend_studio']='little-friends-studio-v1';s['friend_clips']=json.dumps(lib.CLIPS)
for name,(a,b)in lib.CLIPS.items():s.timeline_markers.new(name,frame=a)
s.frame_set(1);s.render.filepath='//three-friends.png';bpy.context.preferences.filepaths.save_version=0
for area in bpy.context.screen.areas:
 if area.type=='DOPESHEET_EDITOR':
  region=next((r for r in area.regions if r.type=='WINDOW'),None)
  if region:
   with bpy.context.temp_override(area=area,region=region):bpy.ops.action.view_all()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'friend_studio.blend'))
if '--no-render'not in sys.argv:bpy.ops.render.render(write_still=True)
# Static, evaluated meshes capture the real shape keys and control poses.
def text(label,pos,size=.22,align='CENTER'):
 d=bpy.data.curves.new(label,'FONT');d.body=label;d.align_x=align;d.size=size;d.extrude=0;d.materials.append(ink);o=bpy.data.objects.new(label,d);sheet.objects.link(o);o.location=(pos[0],1,pos[2]);o.rotation_euler=(math.pi/2,0,0)

if '--sheets'in sys.argv:
 ink=bpy.data.materials.new('Sheet cocoa text');ink.use_nodes=True;nodes=ink.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.12,.06,.09,1);em.inputs[1].default_value=1;ink.node_tree.links.new(em.outputs[0],out.inputs[0])
 for kind,labels in [('expressions',['happy','wink','sleepy','surprised','shy','curious']),('gestures',['wave','dance','bow','celebrate','cuddle','walk'])]:
  sheet=bpy.data.collections.new(kind+' — evaluated poses');s.collection.children.link(sheet)
  for row,style in enumerate(['melody','cinnamoroll','kuromi']):
   _,source_x,char,rig,holder=next(c for c in characters if c[0]==style);rowz=5.1-row*2.4
   text(lib.TITLES[style],(-7.8,-2,rowz+.65),.18,'LEFT')
   for col,name in enumerate(labels):
    first,last=lib.CLIPS[name];phase={'wave':.36,'dance':.30,'celebrate':.375,'walk':.125}.get(name,.5);s.frame_set(round(first+(last-first)*phase));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    size=.62 if style=='cinnamoroll'else .56;transform=Matrix.Translation(Vector(((col-2.5)*2.25,0,rowz)))@Matrix.Scale(size,4)@Matrix.Translation(Vector((-source_x,0,0)))
    for src in char.objects:
     if src.type!='MESH':continue
     evaluated=src.evaluated_get(deps);data=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps);copy=bpy.data.objects.new(style+' '+name+' '+src.name,data);sheet.objects.link(copy);copy.matrix_world=transform@src.matrix_world
  for col,label in enumerate(labels):text(label.capitalize(),((col-2.5)*2.25,-2,7.07),.22)
  text('Little friends · '+kind,(0,-2,7.58),.34)
  for c in stage.objects:
   if c.type=='MESH':c.hide_render=True
  for _,_,char,rig,_ in characters:char.hide_render=True
  # A warm vertical backdrop keeps the sheet evenly lit and free of a horizon.
  backdrop=bpy.data.materials.new('Warm ivory sheet '+kind);backdrop.use_nodes=True;nodes=backdrop.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');emission.inputs[0].default_value=(.86,.74,.77,1);emission.inputs[1].default_value=.7;backdrop.node_tree.links.new(emission.outputs[0],output.inputs[0])
  bpy.ops.mesh.primitive_plane_add(size=2,location=(0,2,3.5),rotation=(math.pi/2,0,0));o=bpy.context.object
  for c in list(o.users_collection):c.objects.unlink(o)
  sheet.objects.link(o);o.scale=(15,6,1);o.data.materials.append(backdrop)
  cam.location=(0,-30,3.3);cam.rotation_euler=(math.pi/2,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=16.2;s.render.resolution_x=1800;s.render.resolution_y=1050;s.eevee.taa_render_samples=64;s.view_settings.exposure=0
  # Broad lights span all rows, including Kuromi's charcoal material.
  for name,pos,power in [('Large warm key',(0,-7,9),900),('Soft cream fill',(-7,-4,4),500),('Pink rim',(7,-3,7),600)]:
   light=bpy.data.objects[name];light.location=pos;light.data.energy=power;light.data.size=7;light.rotation_euler=(Vector((0,0,3.5))-light.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(HERE/(kind+'.png'));bpy.ops.render.render(write_still=True);print('POSE_SHEET_READY',kind,flush=True)
  sheet.hide_render=True
print('FRIEND_STUDIO_READY',flush=True)
