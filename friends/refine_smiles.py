"""Refine only My Melody/Kuromi mouth geometry, retaining their controls and animation.
blender -b --factory-startup --python-exit-code 1 --python friends/refine_smiles.py
"""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import create_friends as creator
for style in ['melody','kuromi']:
 path=HERE/(style+'.blend');original=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
 if s.get('friend_mouth_version')=='soft-stitched-smile-v2':print('SMILE_ALREADY_REFINED',style,flush=True);continue
 s.frame_set(1);bpy.context.view_layer.update();creator.head_z=1.8;creator.head_scale=(.81,.53,.67)
 obj=bpy.data.objects['Embroidered smile'];inverse=obj.matrix_world.inverted();keys=obj.data.shape_keys.key_blocks
 for key in keys:
  verts,_=creator.smile_geometry(key.name,1.47);assert len(verts)==len(key.data)
  for i,p in enumerate(verts):
   local=inverse@Vector(p);key.data[i].co=local
   if key.name=='Basis':obj.data.vertices[i].co=local
 material=creator.mat('Soft mouth embroidery',(.055,.030,.040));node=material.node_tree.nodes.get('Principled BSDF');node.inputs['Roughness'].default_value=.85;node.inputs['Sheen Weight'].default_value=0;node.inputs['Specular IOR Level'].default_value=.12;obj.data.materials.clear();obj.data.materials.append(material);obj.data.update()
 s['friend_mouth_version']='soft-stitched-smile-v2';s['friend_mouth_base_sha256']=original;s['friend_mouth_refinement']='refine_smiles.py'
 bpy.context.preferences.filepaths.save_version=0;s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(path));print('NATURAL_SMILE_READY',style,flush=True)
