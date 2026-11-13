"""Check authored source contacts, planted feet, rest endpoints and old clips.
blender -b together_motions/together_classic.blend --python-exit-code 1 --python verify_together_motions.py
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;style=s['together_style'];source=Path(bpy.data.filepath)
meta=json.loads(source.with_name(style+'.json').read_text());ranges=meta['clips'];unit=meta['actor_scale']*meta['normalize_scale'];floor=meta['floor_source_z']
controls=[o for o in bpy.data.objects if o.name.startswith('CTRL_') and o.type=='EMPTY']
foot_names=['CTRL_Foot_L','CTRL_Foot_R'];s.frame_set(1)
planted={n:bpy.data.objects[n].matrix_world.copy() for n in foot_names}
checks={'style':style,'contacts':{},'grounded_frames':0,'returned_clips':[],'preserved_original_clips':len(json.loads(s['friend_clips'] if style=='melody' else s['kitty_clips']))}
for name,(first,last) in ranges.items():
    s.frame_set(first);bpy.context.view_layer.update();start={o.name:tuple(o.matrix_world) for o in controls}
    # All source sample points, not only contact frames, keep support fixed.
    for frame in range(first,last+1):
        s.frame_set(frame);bpy.context.view_layer.update()
        for n in foot_names:
            delta=bpy.data.objects[n].matrix_world-planted[n]
            assert max(abs(v) for row in delta for v in row)<1e-5,(name,frame,n)
        checks['grounded_frames']+=1
    s.frame_set(last);bpy.context.view_layer.update()
    for o in controls:
        assert max(abs(a-b) for r1,r2 in zip(start[o.name],o.matrix_world) for a,b in zip(r1,r2))<1e-5,(name,o.name,'rest endpoint')
    checks['returned_clips'].append(name)
    if name.startswith('togetherHighfive'):
        side=name[-1];expected=meta['highfive'][side]['contact_actor_local'];errors=[]
        for offset in [24,25,26,27,28,29,30]:
            s.frame_set(first+offset);bpy.context.view_layer.update();p=bpy.data.objects['Together_Palm_'+side].matrix_world.translation
            actual=Vector((p.x*unit,(p.z-floor)*unit,-p.y*unit));errors.append((actual-Vector(expected)).length)
        assert max(errors)<1e-5,(style,side,errors)
        checks['contacts'][side]={'max_error_world':max(errors),'point_actor_local':expected}
assert checks['preserved_original_clips']>=13
source.with_name(style+'-verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print('VERIFIED_TOGETHER',json.dumps(checks),flush=True)
