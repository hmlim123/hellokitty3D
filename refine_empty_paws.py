"""Sculpt a smooth, downward resting arm while preserving the original grip mesh.
The EmptyRest relative key is independent of all existing prop/contact keys.
"""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
VERSION='soft-sides-v2'

def smooth(a,b,value):
 t=max(0,min(1,(value-a)/(b-a)));return t*t*(3-2*t)

def refine_empty_paws():
 s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
 for side,label in [(-1,'L'),(1,'R')]:
  arm=bpy.data.objects['White arm '+str(side)];world=arm.matrix_world.copy();inv=world.inverted()
  basis=arm.data.shape_keys.key_blocks['Basis'];rest=arm.data.shape_keys.key_blocks['EmptyRest']
  points=[world@v.co for v in basis.data];center=sum(points,Vector())/len(points)
  # Undo the bouquet-holding silhouette using a continuous radial cage, then
  # shape one plump oval arm. No thumb/elbow bump is carried into the rest key.
  axis=Vector((-side*.18,-.45,-.26)).normalized()
  lateral=(Vector((1,0,0))-axis*axis.x).normalized();depth=axis.cross(lateral).normalized()
  down=Vector((side*.10,.05,-.43)).normalized()
  out=(Vector((1,0,0))-down*down.x).normalized();front=down.cross(out).normalized()
  target=Vector((side*.98,-.35,1.91));root=bpy.data.objects['CTRL_Arm_'+label].matrix_world.translation.copy()
  for key,p in zip(rest.data,points):
   delta=p-center
   q=Vector((delta.dot(lateral)/.27,delta.dot(depth)/.28,delta.dot(axis)/.48)).normalized()
   length=q.z*.24+.19*math.tanh(q.z*2)/math.tanh(2)
   rounded=target+out*(q.x*.245)+front*(q.y*.25)+down*length
   # Preserve the tucked-in shoulder cap; the lower arm becomes a single oval.
   weight=smooth(.23,.36,(p-root).length)
   key.co=inv@p.lerp(rounded,weight)
  arm['empty_paw_pose']=VERSION
 s['empty_paw_pose']=VERSION;s.frame_set(s.get('default_empty_frame',1105));bpy.context.view_layer.update()
 print('EMPTY_PAW_POSE_REFINED',s.get('plush_variant','classic'),flush=True)

if __name__=='__main__':
 refine_empty_paws();s=bpy.context.scene;style=s.get('plush_variant','classic')
 bpy.context.preferences.filepaths.save_version=0
 path=Path('/tmp/rest-'+style+'.blend')if '--draft'in sys.argv else Path(bpy.data.filepath)
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if '--portrait'in sys.argv:bpy.ops.render.render(write_still=True)
 if '--render'in sys.argv:
  target=Vector((0,-.05,2.80 if style in ['witch','bunny']else 2.45))
  for label,loc in [('front',(0,-15,5.4)),('side',(15,0,5.4)),('three-quarter',(8,-13,5.4))]:
   s.camera.location=loc;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
   s.render.filepath='/tmp/kitty-rest-v2-'+style+'-'+label+'.png';bpy.ops.render.render(write_still=True)
