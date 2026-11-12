"""Export an edited friend without rebuilding or saving over the .blend source.
blender -b friends/melody.blend --python-exit-code 1 --python friends/export_friends.py
"""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;s=bpy.context.scene;source=Path(bpy.data.filepath)
if s.get('friend_version')!='little-friends-v1':raise RuntimeError('Open melody.blend, cinnamoroll.blend or kuromi.blend first.')
style=s['friend_character'];ranges=json.loads(s['friend_clips']);s.frame_start=1;s.frame_end=max(b for a,b in ranges.values());s.frame_set(1);bpy.context.view_layer.update()
char=bpy.data.collections['CHARACTER — '+s['friend_title']];rig=bpy.data.collections['CONTROLS — pose these']
bpy.ops.object.select_all(action='DESELECT')
for o in [*char.objects,*rig.objects]:o.select_set(True)
asset=source.with_suffix('.glb')
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='SCENE',export_frame_range=True,export_force_sampling=True,export_cameras=False,export_lights=False,export_morph=True)
sys.path.insert(0,str(HERE/'game_export_helpers'))
if not (HERE/'game_export_helpers').exists():sys.path.insert(0,str(HERE.parent/'game_export_helpers'))
from glb_clips import split_clips
split_clips(asset,ranges,s.render.fps)
points=[o.matrix_world@Vector(c) for o in char.objects if o.type=='MESH'for c in o.bound_box];low=[min(p[i]for p in points)for i in range(3)];high=[max(p[i]for p in points)for i in range(3)]
triangles=0
for o in char.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
meta={'version':1,'character':style,'title':s['friend_title'],'source_file':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fps':s.render.fps,'clips':ranges,'morphs':{o.name:[k.name for k in o.data.shape_keys.key_blocks if k.name!='Basis']for o in char.objects if o.type=='MESH'and o.data.shape_keys},'bounds_y_up':{'min':[low[0],low[2],-high[1]],'max':[high[0],high[2],-low[1]]},'source_triangles':triangles,'bytes':asset.stat().st_size,'held_item':None,'author_script_sha256':hashlib.sha256((HERE/'create_friends.py').read_bytes()).hexdigest(),'export_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
asset.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print('EXPORTED_FRIEND',style,triangles,'triangles',asset.stat().st_size,'bytes',flush=True)
