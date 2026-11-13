import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent/'together_motions';s=bpy.context.scene
neutral='--neutral' in sys.argv
pose_offset=0 if neutral else 24
s.frame_set(1717+pose_offset);bpy.context.view_layer.update()
for collection in bpy.data.collections:
 if collection.name not in ['HELLO KITTY — editable parts','ANIMATION — select controls to pose']:
  collection.hide_render=True
for o in list(bpy.data.objects):
 if o.animation_data:o.animation_data_clear()
 if o.type=='MESH' and o.data.shape_keys:o.data.shape_keys.animation_data_clear()
kroot=bpy.data.objects['CTRL_Root'];wrap=bpy.data.objects.new('Preview Kitty normalized',None);s.collection.objects.link(wrap)
kroot.parent=wrap
meta=json.loads((root/'classic.json').read_text());u=meta['normalize_scale']*.78
wrap.scale=(u,u,u);wrap.location=(0,.42,-meta['floor_source_z']*u)
existing=set(bpy.data.objects)
with bpy.data.libraries.load(str(root/'together_melody.blend'),link=False) as (a,b):
 b.collections=[name for name in a.collections if name in ['CHARACTER — My Melody','CONTROLS — pose these']]
for collection in b.collections:s.collection.children.link(collection)
s.frame_set(1609+pose_offset);bpy.context.view_layer.update()
new=[o for o in bpy.data.objects if o not in existing]
mr=next(o for o in new if o.name.startswith('CTRL_Root'))
mwrap=bpy.data.objects.new('Preview Melody normalized',None);s.collection.objects.link(mwrap);mr.parent=mwrap
meta=json.loads((root/'melody.json').read_text());u=meta['normalize_scale']*.78
mwrap.scale=(u,u,u);mwrap.rotation_euler.z=math.pi;mwrap.location=(0,-.42,-meta['floor_source_z']*u)
for o in bpy.data.objects:
 p=o
 while p:
  if p.name.startswith('CTRL_Bouquet'):o.hide_render=True;break
  p=p.parent
# A clean broad studio light, no added grain or stochastic shadow speckles.
world=bpy.data.worlds.new('Together preview pastel');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.70,.78,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;s.world=world
for name,loc,power,size in [('Together key',(2,-4,5),450,5),('Together fill',(-3,2,4),350,4)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.use_shadow=False;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Together preview camera');cam=bpy.data.objects.new('Together preview camera',d);s.collection.objects.link(cam);s.camera=cam;cam.location=(4,-.8,2.2);target=Vector((0,0,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=3.3
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32;s.render.resolution_x=850;s.render.resolution_y=850;s.render.resolution_percentage=100;s.render.filepath=str(root/('highfive-neutral.png' if neutral else 'highfive-partners.png'));bpy.ops.render.render(write_still=True)
