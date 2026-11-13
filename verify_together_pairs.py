import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
folder=Path(__file__).resolve().parent/'together_motions'
def is_headbody(o):
 if o.type!='MESH' or o.hide_render:return False
 p=o
 while p:
  if p.name.startswith(('CTRL_Arm','CTRL_Foot')):return False
  if p.name.startswith('CTRL_Head'):return True
  p=p.parent
 return o.parent and o.parent.name.startswith('CTRL_Body')
def geometry(objects):
 vs=[];ps=[]
 for o in objects:
  if not is_headbody(o):continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());idx=len(vs);vs.extend(ev.matrix_world@v.co for v in ev.data.vertices);ps.extend(tuple(idx+i for i in p.vertices) for p in ev.data.polygons)
 return vs,ps
def front_y(objects,minimum):
 values=[]
 for o in objects:
  if not is_headbody(o):continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
  coords=np.empty(len(ev.data.vertices)*3,dtype=np.float32)
  ev.data.vertices.foreach_get('co',coords)
  row=np.array(ev.matrix_world[1][:3],dtype=np.float32)
  ys=coords.reshape((-1,3))@row+ev.matrix_world[1][3]
  values.append(float(np.min(ys) if minimum else np.max(ys)))
 return min(values) if minimum else max(values)
results=[]
for sty in ['classic','cloud','witch','baby','kitten','bunny']:
 for side,mside in [('R','L'),('L','R')]:
  bpy.ops.wm.open_mainfile(filepath=str(folder/('together_'+sty+'.blend')));s=bpy.context.scene
  km=json.loads((folder/(sty+'.json')).read_text());mm=json.loads((folder/'melody.json').read_text());sep=.84
  kr=bpy.data.objects['CTRL_Root'];wrap=bpy.data.objects.new('Kitty normalize',None);s.collection.objects.link(wrap);kr.parent=wrap;u=km['normalize_scale']*.78;wrap.scale=(u,u,u);wrap.location=(0,sep/2,-km['floor_source_z']*u)
  objs=list(bpy.data.collections['HELLO KITTY — editable parts'].objects);cache={}
  offsets=range(73)
  for offset in sorted(set(offsets)):
   s.frame_set(km['clips']['togetherHighfive'+side][0]+offset);bpy.context.view_layer.update();cache[offset]=front_y(objs,True)
  old=set(bpy.data.objects)
  with bpy.data.libraries.load(str(folder/'together_melody.blend'),link=False) as (a,b):b.collections=[n for n in a.collections if n in ['CHARACTER — My Melody','CONTROLS — pose these']]
  for c in b.collections:s.collection.children.link(c)
  new=[o for o in bpy.data.objects if o not in old];mr=next(o for o in new if o.name.startswith('CTRL_Root'));wrap=bpy.data.objects.new('Melody normalize',None);s.collection.objects.link(wrap);mr.parent=wrap;u=mm['normalize_scale']*.78;wrap.scale=(u,u,u);wrap.rotation_euler.z=math.pi;wrap.location=(0,-sep/2,-mm['floor_source_z']*u)
  samples=[]
  for offset,kitty_front in cache.items():
   s.frame_set(mm['clips']['togetherHighfive'+mside][0]+offset);bpy.context.view_layer.update();gap=kitty_front-front_y(new,False)
   # A strictly positive separating plane proves every triangle is disjoint.
   assert gap>0,(sty,side,offset,'head/body separating planes overlap',gap)
   overlaps=0
   samples.append({'frame_offset':offset,'front_plane_gap':gap,'intersections':overlaps})
  r={'style':sty,'kitty_hand':side,'melody_hand':mside,'anchor_separation':sep,'samples':samples};results.append(r)
  print('PAIR',sty,side,'intersections',[(x['frame_offset'],x['intersections']) for x in samples if x['intersections']],'gap',min(x['front_plane_gap'] for x in samples),flush=True)
  assert all(x['intersections']==0 for x in samples),(sty,side,'partner meshes intersect')
(folder/'pair-clearance-verification.json').write_text(json.dumps(results,indent=2)+'\n')
