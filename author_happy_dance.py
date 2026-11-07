"""Author a six-second happy step-touch dance, plus a matching occupied-paw take.
Keeps the existing contact performances and original frame-1 bind pose intact.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler
VERSION='happy-step-v1'
START=1153;LENGTH=144;HELD_START=1309

def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def between(a,b,t):return smooth((t-a)/(b-a))
def sample(keys,frame):
 for (a,x),(b,y)in zip(keys,keys[1:]):
  if frame<=b:return x+(y-x)*smooth((frame-a)/(b-a))
 return keys[-1][1]
def clear_range(data):
 if not data.animation_data or not data.animation_data.action:return
 for curve in data.animation_data.action.fcurves:
  for key in list(curve.keyframe_points):
   if START<=key.co.x<=HELD_START+LENGTH:curve.keyframe_points.remove(key,fast=True)
  curve.update()

def author_happy_dance():
 s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();style=s.get('plush_variant','classic')
 energy={'classic':1,'cloud':1.04,'witch':.97,'baby':.94,'kitten':1.02,'bunny':.98}[style]
 phase={'classic':0,'cloud':.08,'witch':.20,'baby':.30,'kitten':.12,'bunny':.24}[style]
 names=['CTRL_Root','CTRL_Body','CTRL_Head','CTRL_Bouquet','CTRL_Arm_L','CTRL_Arm_R','CTRL_Foot_L','CTRL_Foot_R']
 controls={n:bpy.data.objects[n]for n in names};base={n:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy())for n,o in controls.items()}
 extras=[o for o in bpy.data.collections['ANIMATION — select controls to pose'].objects if o.name.startswith('CTRL_Plush')]
 extra_base={o.name:o.rotation_euler.copy()for o in extras}
 eyes=[bpy.data.objects['Eye left'],bpy.data.objects['Eye right']];arms=[bpy.data.objects['White arm -1'],bpy.data.objects['White arm 1']]
 for o in [*controls.values(),*extras]:clear_range(o)
 for o in eyes+arms:clear_range(o.data.shape_keys)
 foot_data={}
 for side,label in [(-1,'L'),(1,'R')]:
  ctrl=controls['CTRL_Foot_'+label];mesh=bpy.data.objects['Foot '+str(side)];points=[ctrl.matrix_world.inverted()@(mesh.matrix_world@v.co)for v in mesh.data.vertices]
  foot_data[label]=(ctrl.matrix_world.translation.copy(),points,min((mesh.matrix_world@v.co).z for v in mesh.data.vertices))
 step=.28*energy
 lx=[(0,0),(12,-step),(24,-step),(36,-step),(48,step),(60,-step),(72,-step),(84,-step),(96,0)]
 rx=[(0,0),(12,0),(24,-step),(36,step),(48,step),(60,step),(72,-step),(84,0),(96,0)]
 hips=[(0,0),(12,-step),(24,-step),(36,step),(48,step),(60,-step),(72,-step),(84,0),(96,0)]
 moving=['L','R','R','L','L','R','R','L']
 for held,start in [(False,START),(True,HELD_START)]:
  for f in range(LENGTH+1):
   frame=start+f;s.frame_set(frame)
   for name,o in controls.items():o.location=base[name][0];o.rotation_euler=base[name][1];o.scale=base[name][2]
   enter=between(0,10,f);exit=1-between(126,144,f);engage=enter*exit
   segment=min(7,int(f//12));p=(f-segment*12)/12 if f<96 else 1
   if f<96:
    (a,x),(b,y)=hips[segment],hips[segment+1]
    hip=x+(y-x)*between(.18,1,p)
    if abs(y-x)>.001:hip-=math.copysign(.025*math.sin(math.pi*min(1,p/.18)),y-x)
   else:hip=0
   hop=0
   if 96<=f<120:hop=.22*energy*math.sin(math.pi*((f-96)%12)/12)**2
   beat=f/12;load=math.sin(math.pi*p)**2 if f<96 else 0
   root=controls['CTRL_Root'];root.location=base['CTRL_Root'][0]+Vector((hip,0,hop));root.rotation_euler.z=.32*(hip/step)
   body=controls['CTRL_Body'];body.rotation_euler=(.035*math.sin(math.tau*beat)*engage,.10*(hip/step),0)
   body.location.z=base['CTRL_Body'][0].z-.025*load
   if 96<=f<120:body.scale=(1+.018*math.cos(math.tau*(f-96)/12),1+.018*math.cos(math.tau*(f-96)/12),1-.025*math.cos(math.tau*(f-96)/12))
   if f>=120:body.rotation_euler.x+=.12*math.sin(math.pi*between(124,144,f))
   head=controls['CTRL_Head'];head.rotation_euler=(.045*math.sin(math.tau*beat-.3)*engage,-.065*math.sin(math.pi*beat+phase)*engage,-.055*(hip/step))
   for side,label in [(-1,'L'),(1,'R')]:
    arm=controls['CTRL_Arm_'+label]
    raise_paw=(.88+.48*math.sin(math.pi*beat+(0 if side<0 else math.pi)+phase))*engage
    if f>=96:raise_paw=sample([(96,1.28),(102,1.62),(108,1.25),(114,1.62),(120,1.50),(128,.8),(144,0)],f)*energy
    if not held:arm.rotation_euler=(-.13*math.sin(math.pi*beat)*engage,-side*raise_paw,-side*.09*math.sin(math.pi*beat+phase)*engage)
   bpy.context.view_layer.update()
   for side,label in [(-1,'L'),(1,'R')]:
    bind,points,floor=foot_data[label];ctrl=controls['CTRL_Foot_'+label]
    swing=math.sin(math.pi*min(1,p/.85))**2 if f<96 and moving[segment]==label else 0
    lift=hop+.15*energy*swing
    path=lx if label=='L'else rx
    offset=path[segment][1]+(path[segment+1][1]-path[segment][1])*between(0,.85,p) if f<96 else 0
    world_rot=Euler((.13*swing,side*.025*swing,.112*offset/step),'XYZ').to_matrix()
    pos=bind+Vector((offset,-.035*swing,0))
    pos.z=floor+lift-min((world_rot@point).z for point in points)
    world=world_rot.to_4x4();world.translation=pos;ctrl.matrix_world=world
   for name,o in controls.items():
    for prop in ['location','rotation_euler','scale']:o.keyframe_insert(prop,frame=frame)
   for o in extras:
    secondary=(.025*math.sin(math.pi*beat-.55)*engage,.04*math.sin(math.pi*beat-.7+phase)*engage,.018*math.sin(math.pi*beat-.9)*engage)
    o.rotation_euler=tuple(extra_base[o.name][i]+secondary[i]for i in range(3));o.keyframe_insert('rotation_euler',frame=frame)
   smile=between(4,14,f)*(1-between(124,142,f))
   for eye in eyes:
    for key in eye.data.shape_keys.key_blocks:
     if key.name in ['Sleepy','Surprise','SoftSmile','Shy','Curious']:
      key.value=smile if key.name=='SoftSmile'else 0;key.keyframe_insert('value',frame=frame)
   for arm in arms:
    for key in arm.data.shape_keys.key_blocks:
     if key.name in ['EmptyRest','Elbow_soft','Paw_soft']:
      key.value=(0 if held else 1)if key.name=='EmptyRest'else 0;key.keyframe_insert('value',frame=frame)
 # Dense new motion samples interpolate linearly; no toe overshoot between poses.
 for data in [*controls.values(),*extras,*[o.data.shape_keys for o in eyes+arms]]:
  if data.animation_data and data.animation_data.action:
   for curve in data.animation_data.action.fcurves:
    for key in curve.keyframe_points:
     if START<=key.co.x<=HELD_START+LENGTH:key.interpolation='LINEAR'
 clips=json.loads(s['kitty_clips']);clips['dance']=[START,START+LENGTH];clips['danceHeld']=[HELD_START,HELD_START+LENGTH];s['kitty_clips']=json.dumps(clips)
 s['dance_library']=VERSION;s['dance_guide']='Six seconds at 24fps: grounded step-touches, broad alternating paw swings, two happy hops, smiling eyes and a cheer/bow finish. dance 1153–1297; occupied-paw take 1309–1453. Legacy 1–49 preserved. Default empty-arm frame 1105 unchanged.'
 s.frame_end=HELD_START+LENGTH;s.frame_set(s.get('default_empty_frame',1105));bpy.context.view_layer.update()
 print('HAPPY_DANCE_AUTHORED',style,flush=True)

if __name__=='__main__':
 author_happy_dance();s=bpy.context.scene;style=s.get('plush_variant','classic');bpy.context.preferences.filepaths.save_version=0
 path=Path('/tmp/happy-dance-'+style+'.blend')if '--draft'in sys.argv else Path(bpy.data.filepath)
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if '--preview'in sys.argv:
  s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=8;s.render.resolution_x=480;s.render.resolution_y=480
  for label,offset in [('left-step',12),('right-step',36),('cheer',114),('finish',144)]:
   s.frame_set(START+offset);s.render.filepath='/tmp/kitty-happy-dance-'+style+'-'+label+'.png';bpy.ops.render.render(write_still=True)
