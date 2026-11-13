"""Export an edited together source; never rebuild or save the .blend input.
blender -b together_motions/together_melody.blend --python-exit-code 1 --python export_together_motions.py
"""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
s=bpy.context.scene;source=Path(bpy.data.filepath)
if s.get('together_library')!='together-v1': raise RuntimeError('Open together_motions/together_*.blend')
style=s['together_style'];ranges=json.loads(s['together_clips'])
rig=bpy.data.collections['CONTROLS — pose these' if style=='melody' else 'ANIMATION — select controls to pose']
s.frame_start=1;s.frame_end=max(last for first,last in ranges.values());s.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for o in rig.objects:
    if o.type=='EMPTY' and o.name.startswith(('CTRL_', 'Together_')):o.select_set(True)
asset=source.parent/(style+'.glb')
# Record the actual occupied-paw paths so the game can place each small bowl
# and decorating board under its own reachable hand, rather than mid-room.
baking={};unit=s['together_norm']*.78;floor=s['together_floor']
def actor(p):return [p.x*unit,(p.z-floor)*unit,-p.y*unit]
for name in ['togetherStir','togetherDecorate','togetherPresent']:
    first,last=ranges[name];samples={side:[] for side in ['L','R']}
    for frame in range(first+math.ceil((last-first)/3),first+math.floor((last-first)*.6)+1):
        s.frame_set(frame);bpy.context.view_layer.update()
        for side in ['L','R']:samples[side].append(actor(bpy.data.objects['Together_Grip_'+side].matrix_world.translation))
    baking[name]={'reach_time':(last-first)/s.render.fps/3,'return_time':(last-first)/s.render.fps*.875,'hands':{side:{'actor_local':samples[side][0],'bounds_actor_local':{'min':[min(p[i] for p in samples[side]) for i in range(3)],'max':[max(p[i] for p in samples[side]) for i in range(3)]}} for side in ['L','R']}}
s.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_extras=False,export_animations=True,export_animation_mode='SCENE',export_frame_range=True,export_force_sampling=True,export_cameras=False,export_lights=False)
sys.path.insert(0,str(ROOT/'game_export_helpers'));from glb_clips import split_clips
split_clips(asset,ranges,s.render.fps)
meta={'version':1,'library':'together-v1','style':style,'source_file':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_source':s['together_original_source'],'original_source_sha256':s['together_original_sha256'],'author_script':'author_together_motions.py','author_sha256':hashlib.sha256((ROOT/'author_together_motions.py').read_bytes()).hexdigest(),'export_script':'export_together_motions.py','export_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fps':s.render.fps,'clips':ranges,'durations':{n:(b-a)/s.render.fps for n,(a,b) in ranges.items()},'actor_scale':.78,'normalize_scale':s['together_norm'],'floor_source_z':s['together_floor'],'contact_time':1.0,'contact_hold_until':1.25,'highfive':json.loads(s['together_contact']),'rest_translations_y_up':json.loads(s['together_rest_offsets']),'grips':{side:{'control':'CTRL_Arm_'+side,'socket':'Together_Grip_'+side,'local_y_up':json.loads(s['together_rest_offsets'])['Together_Grip_'+side]} for side in ['L','R']},'occupied_clips':['togetherStir','togetherDecorate','togetherPresent'],'bytes':asset.stat().st_size,'notes':'Controller-only library. Subtract loader bind translations for all controls inside additive pivots. All clips retain static rest channels. Kitty occupied clips need EmptyRest=0 at full reach; interpolate it with the authored envelope. Palm coordinates are actual relaxed mesh surfaces, before normalization; contact_actor_local includes normalization and actor scale.'}
meta['baking']=baking
asset.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
print('EXPORTED_TOGETHER',style,asset.stat().st_size,flush=True)
