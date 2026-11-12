"""Render a close review of the actual revised neutral/happy facial geometry."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import create_friends as lib
bpy.ops.wm.read_factory_settings(use_empty=False);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):bpy.data.collections.remove(col)
stage=bpy.data.collections.new('Smile review studio');bpy.context.scene.collection.children.link(stage);lib.stage=stage;lib.style='melody';lib.studio();s=bpy.context.scene
for o in list(stage.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
ink=lib.mat('Review cocoa',(.11,.05,.075));p=ink.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.11,.05,.075,1);p.inputs['Emission Strength'].default_value=.6
for style,x in [('melody',-1.06),('kuromi',1.06)]:
 with bpy.data.libraries.load(str(HERE/(style+'.blend')))as(src,dst):dst.collections=['CHARACTER — '+lib.TITLES[style],'CONTROLS — pose these']
 char,rig=dst.collections
 for col in [char,rig]:s.collection.children.link(col)
 for label,frame,z in [('Relaxed',1,2.3),('Happy',877,.5)]:
  s.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();transform=Matrix.Translation(Vector((x,0,z-1.8)))
  for obj in char.objects:
   if not(obj.name.startswith(('Head','Ivory face','Eye ','Button nose','Embroidered smile','Pink cheek','Pink skull','Skull '))):continue
   data=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),depsgraph=deps);copy=bpy.data.objects.new(style+' '+label+' '+obj.name,data);stage.objects.link(copy);copy.matrix_world=transform@obj.matrix_world
  curve=bpy.data.curves.new(style+' '+label,'FONT');curve.body=lib.TITLES[style]+' · '+label.lower();curve.align_x='CENTER';curve.size=.13;curve.materials.append(ink);text=bpy.data.objects.new(curve.body,curve);stage.objects.link(text);text.location=(x,1,z-.80);text.rotation_euler=(math.pi/2,0,0)
 char.hide_render=True
bg=bpy.data.materials.new('Review rose backdrop');bg.use_nodes=True;n=bg.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.86,.74,.77,1);em.inputs[1].default_value=.8;bg.node_tree.links.new(em.outputs[0],out.inputs[0]);bpy.ops.mesh.primitive_plane_add(size=20,location=(0,2,1.5),rotation=(math.pi/2,0,0));bpy.context.object.data.materials.append(bg)
cam=s.camera;cam.location=(0,-12,1.5);cam.rotation_euler=(math.pi/2,0,0);cam.data.ortho_scale=4.6;s.render.resolution_x=1200;s.render.resolution_y=1000;s.eevee.taa_render_samples=64;s.render.filepath=str(HERE/'natural-smiles.png');bpy.ops.render.render(write_still=True);print('NATURAL_SMILE_REVIEW_RENDERED',flush=True)
