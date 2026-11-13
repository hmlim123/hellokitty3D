"""Verify the two shared rigs retain attached rounded shoulder caps at all high-five frames."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent/'together_motions'
results=[]
for sty in ['classic','melody']:
 bpy.ops.wm.open_mainfile(filepath=str(r/('together_'+sty+'.blend')));s=bpy.context.scene
 def geo(obs):
  vs=[];ps=[]
  for o in obs:
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());i=len(vs);vs.extend(ev.matrix_world@v.co for v in ev.data.vertices);ps.extend(tuple(i+j for j in p.vertices) for p in ev.data.polygons)
  return BVHTree.FromPolygons(vs,ps),vs
 for side,first in [('L',1609),('R',1717)]:
  arm=bpy.data.objects['Relaxed paw '+side if sty=='melody' else ('White arm -1' if side=='L' else 'White arm 1')]
  supports=[bpy.data.objects[n] for n in (['Plush body','Head'] if sty=='melody' else ['Head','Strawberry pink rounded dress','Pink shoulder -1','Pink shoulder 1'])]
  samples=[]
  for off in range(73):
   s.frame_set(first+off);bpy.context.view_layer.update();a,av=geo([arm]);b,bv=geo(supports);cross=len(a.overlap(b));gap=0 if cross else min(b.find_nearest(v)[3] for v in av);samples.append({'offset':off,'intersections':cross,'gap_source':gap})
  print('ATTACHED',sty,side,'maxgap',max(x['gap_source'] for x in samples),'nointersections',[(x['offset'],x['gap_source']) for x in samples if not x['intersections']],flush=True)
  assert all(x['intersections']>0 for x in samples),(sty,side,'upper paw cap is detached')
  results.append({'style':sty,'side':side,'samples':samples})
(r/'shoulder-attachment-verification.json').write_text(json.dumps(results,indent=2)+'\n')
