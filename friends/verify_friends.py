"""Check the actual editable projects and their exported animation/morph data."""
import bpy,json,math,struct,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
report=[]
for style in ['melody','cinnamoroll','kuromi']:
 source=HERE/(style+'.blend');bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;clips=json.loads(s['friend_clips']);assert len(clips)==13 and s.render.fps==24
 char=bpy.data.collections['CHARACTER — '+s['friend_title']];controls=bpy.data.collections['CONTROLS — pose these'];assert all(bpy.data.objects.get(n)for n in ['CTRL_Root','CTRL_Head','CTRL_Arm_L','CTRL_Arm_R','CTRL_Foot_L','CTRL_Foot_R','CTRL_Ear_L','CTRL_Ear_R'])
 def pose(frame):s.frame_set(frame);bpy.context.view_layer.update()
 pose(1)
 for o in controls.objects:assert all(abs(v)<1e-6 for v in o.rotation_euler)
 for o in char.objects:
  assert o.type=='MESH' and not o.particle_systems
  if o.data.shape_keys:assert all(abs(k.value)<1e-6 for k in o.data.shape_keys.key_blocks if k.name!='Basis')
  if 'ear 'in o.name.lower():
   o.data.calc_loop_triangles();volume=sum(o.data.vertices[t.vertices[0]].co.dot(o.data.vertices[t.vertices[1]].co.cross(o.data.vertices[t.vertices[2]].co))for t in o.data.loop_triangles)/6;assert volume>0,(style,o.name,volume)
 for name,(first,last)in clips.items():
  for f in [first,(first+last)//2,last]:
   pose(f)
   for o in controls.objects:assert all(math.isfinite(v)for row in o.matrix_world for v in row)
   for side in ['L','R']:
    foot=bpy.data.objects['Foot '+side];floor=min((foot.matrix_world@Vector(c)).z for c in foot.bound_box);assert floor>=-.0001,(style,name,f,floor)
 if style!='cinnamoroll':
  assert s.get('friend_mouth_version')=='soft-stitched-smile-v2'
  mouth=bpy.data.objects['Embroidered smile'];points=[mouth.matrix_world@v.co for v in mouth.data.vertices]
  assert max(p.x for p in points)-min(p.x for p in points)<.165
  for p in points:
   surface=-.53*math.sqrt(max(.025,1-(p.x/.81)**2-((p.z-1.8)/.67)**2))-.012
   assert -.0011<surface-p.y<.0115,(style,'floating smile',surface-p.y)
  centers=[sum((points[i*8+j].z for j in range(8)))/8 for i in range(33)]
  assert all(centers[i]>centers[i+1]for i in range(16))
  assert all(centers[i]<centers[i+1]for i in range(16,32))
 pose(61)
 for name in ['Eye left','Eye right']:assert bpy.data.objects[name].data.shape_keys.key_blocks['Blink'].value>.99
 pose(961);left=bpy.data.objects['Eye left'].data.shape_keys.key_blocks;right=bpy.data.objects['Eye right'].data.shape_keys.key_blocks;assert right['Blink'].value>.99 and left['Blink'].value<.001 and right['SoftSmile'].value<.001
 pose(877)
 for name in ['Eye left','Eye right','Embroidered smile']:assert bpy.data.objects[name].data.shape_keys.key_blocks['SoftSmile'].value>.99
 pose(1165)
 for name in ['Eye left','Eye right','Embroidered smile']:assert bpy.data.objects[name].data.shape_keys.key_blocks['Surprise'].value>.99
 positions=[]
 for f in range(217,362,3):pose(f);positions.append(bpy.data.objects['CTRL_Root'].location.copy())
 assert max(p.x for p in positions)-min(p.x for p in positions)>.28
 assert max(p.z for p in positions)>.05
 pose(517)
 assert abs(bpy.data.objects['CTRL_Arm_R'].rotation_euler.y)>1.5
 pose(1)
 if style=='cinnamoroll':assert bpy.data.objects.get('Cinnamon roll tail') and bpy.data.objects.get('Rounded tail end')
 if style=='kuromi':assert len([o for o in char.objects if o.name.startswith('Skull tooth')])==3
 asset=HERE/(style+'.glb');meta=json.loads(asset.with_suffix('.json').read_text());assert meta['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest();assert meta['author_script_sha256']==hashlib.sha256((HERE/'create_friends.py').read_bytes()).hexdigest()
 data=asset.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);offset=20+n;blob=data[offset+8:];assert len(doc['animations'])==13
 def read(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];assert a['componentType']==5126
  return struct.unpack_from('<'+'f'*(a['count']*width),blob,v.get('byteOffset',0)+a.get('byteOffset',0))
 for a in doc['animations']:
  assert a['name']in clips and a['channels'];expected=(clips[a['name']][1]-clips[a['name']][0])/24
  for sampler in a['samplers']:
   times=read(sampler['input']);assert abs(times[0])<1e-5 and abs(times[-1]-expected)<1e-4;assert all(math.isfinite(v)for v in read(sampler['output']))
  assert any(c['target']['path']=='weights'for c in a['channels'])
 names=[o.get('name','')for o in doc['nodes']];assert not any('Studio'in n or 'camera'in n.lower()for n in names)
 triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes']for p in m['primitives']);assert triangles<40000 and len(data)<2000000
 report.append({'character':style,'source':source.name,'source_sha256':meta['source_sha256'],'triangles':triangles,'bytes':len(data),'clips':len(clips),'checks':'neutral/rest, outward ears, grounded feet, full blink/wink, facial morphs, visible dance/hops, raised cheer paws, export clips and provenance'})
 print('VERIFIED_FRIEND',style,triangles,len(data),'13 clips',flush=True)
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('ALL_THREE_FRIENDS_VERIFIED',flush=True)
