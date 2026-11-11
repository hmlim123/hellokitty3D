"""Export edited home performances without rebuilding or saving the source.
blender -b home_motions/kitty_home_classic.blend --python-exit-code 1 --python export_home_motions.py
"""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;source=Path(bpy.data.filepath);s=bpy.context.scene
if s.get('home_motion_library')!='cozy-home-v1':raise RuntimeError('Open a kitty_home_*.blend project first.')
style=s.get('plush_variant','classic');ranges=json.loads(s['home_clips']);norm=2.27/s.get('plush_body_height',4.56808);scale=.9
s.frame_set(1);bpy.context.view_layer.update();root=bpy.data.objects['CTRL_Root'];bind=root.matrix_world.translation.copy();foot=bpy.data.objects['Foot -1'];floor=min((foot.matrix_world@Vector(c)).z for c in foot.bound_box)
s.frame_set(61);bpy.context.view_layer.update();p=bpy.data.objects['Socket_Teacup'].matrix_world.translation;cup=[p.x*norm*scale,(p.z-floor)*norm*scale+.145,-p.y*norm*scale];rise=(root.matrix_world.translation.z-bind.z)*norm*scale
s.frame_start=1;s.frame_end=max(end for _,end in ranges.values());s.frame_set(1);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.collections['ANIMATION — select controls to pose'].objects:
 if o.type=='EMPTY':o.select_set(True)
asset=source.parent/f'{style}.glb'
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='SCENE',export_frame_range=True,export_force_sampling=True,export_cameras=False,export_lights=False)
helpers=ROOT/'game_export_helpers'
if not helpers.is_dir():helpers=ROOT.parent/'hellokittygame'/'scripts'
sys.path.insert(0,str(helpers));from glb_clips import split_clips
split_clips(asset,ranges,s.render.fps)
try:filename=str(source.relative_to(ROOT))
except ValueError:filename=source.name
meta={'version':1,'library':'cozy-home-v1','style':style,'source_file':filename,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_source':s['home_original_source'],'original_source_sha256':s['home_original_sha256'],'script':'author_home_motions.py','script_sha256':hashlib.sha256((ROOT/'author_home_motions.py').read_bytes()).hexdigest(),'export_script':Path(__file__).name,'export_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fps':24,'clips':ranges,'cup_rest':cup,'root_rise':rise,'web_scale':scale,'normalize_scale':norm,'bytes':asset.stat().st_size}
asset.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
print('HOME_MOTION_EXPORTED',style,asset.stat().st_size,'cup',cup,flush=True)
