"""Build three original editable, smoothly shaded plush-style character projects.
Blender 4.3+: blender -b --factory-startup --python-exit-code 1 --python friends/create_friends.py
Use --character melody|cinnamoroll|kuromi to author one project. Existing Kitty files are untouched.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
FPS=24
CLIPS={'idle':[1,97],'wave':[121,193],'dance':[217,361],'bow':[385,457],
       'celebrate':[481,577],'cuddle':[601,697],'walk':[721,817],
       'happy':[841,913],'wink':[937,985],'sleepy':[1009,1105],
       'surprised':[1129,1201],'shy':[1225,1321],'curious':[1345,1441]}
TITLES={'melody':'My Melody','cinnamoroll':'Cinnamoroll','kuromi':'Kuromi'}
COLORS={'melody':(.91,.34,.53),'cinnamoroll':(.49,.75,.86),'kuromi':(.32,.24,.42)}
FACE_KEYS=['Blink','SoftSmile','Sleepy','Surprise','Shy','Curious']

def mat(name,color,cloth=True):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Roughness'].default_value=.73 if cloth else .38
 p.inputs['Specular IOR Level'].default_value=.23 if cloth else .33
 p.inputs['Sheen Weight'].default_value=.18 if cloth else 0
 return m

def link(o,col):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
 return o

def parent(o,control):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=control;o.matrix_world=world
 return o

def ball(name,pos,scale,material,control=None,segments=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
 o=link(bpy.context.object,char);o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 if control:parent(o,control)
 return o

def mesh(name,verts,faces,material,control=None):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);char.objects.link(o);d.materials.append(material)
 for p in d.polygons:p.use_smooth=True
 if control:parent(o,control)
 return o

def tube(name,points,radius,material,control=None):
 verts=[];faces=[];points=[Vector(p)for p in points];sides=8
 for i,p in enumerate(points):
  tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
  normal=tangent.cross(Vector((0,1,0))).normalized();bi=tangent.cross(normal).normalized()
  for j in range(sides):
   a=j*math.tau/sides;verts.append(p+radius*(normal*math.cos(a)+bi*math.sin(a)))
 for i in range(len(points)-1):
  for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
 faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+j for j in range(sides))])
 return mesh(name,verts,faces,material,control)

def control(name,pos,par=None):
 o=bpy.data.objects.new(name,None);rig.objects.link(o);o.empty_display_type='CIRCLE';o.empty_display_size=.15;o.location=pos
 if par:parent(o,par)
 return o

def catmull(vals,t):
 k=min(len(vals)-2,int(t*(len(vals)-1)));u=t*(len(vals)-1)-k
 a,b,c,d=[vals[max(0,min(len(vals)-1,j))]for j in [k-1,k,k+1,k+2]]
 return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

def ear(name,path,widths,thickness,material,ctrl):
 points=[Vector(p)for p in path];verts=[];faces=[];steps=40;sides=20
 for i in range(steps+1):
  t=i/steps;p=catmull(points,t);before=catmull(points,max(0,t-.002));after=catmull(points,min(1,t+.002));direction=(after-before).normalized();across=Vector((-direction.z,0,direction.x)).normalized()
  w=max(.001,catmull(widths,t));h=max(.001,catmull(thickness,t))
  if widths[-1]<.005:
   # One continuous rounded profile avoids a separate-looking cap or pinched hem.
   cap=math.sqrt(max(.000001,1-t**6));ease=math.sin(t*math.pi/2)
   w=(widths[0]+(max(widths)-widths[0])*ease)*cap
   h=(thickness[0]+(max(thickness)-thickness[0])*ease)*cap
  for j in range(sides):
   a=j*math.tau/sides;verts.append(p+across*(w*math.cos(a))+Vector((0,-h*math.sin(a),0)))
 for i in range(steps):
  for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
 faces.extend([tuple(range(sides-1,-1,-1)),tuple(steps*sides+j for j in range(sides))])
 return mesh(name,verts,faces,material,ctrl)

def front(x,z,offset=.012):
 return -head_scale[1]*math.sqrt(max(.025,1-(x/head_scale[0])**2-((z-head_z)/head_scale[2])**2))-offset

def face_patch(name,center,rx,rz,material,notch=0):
 verts=[(0,front(0,center),center)];faces=[];rings=12;sides=64
 for r in range(1,rings+1):
  u=r/rings
  for j in range(sides):
   a=j*math.tau/sides;x=rx*math.sin(a);z=rz*math.cos(a)
   if math.cos(a)>0:z-=notch*math.exp(-(x/.22)**2)
   x*=u;z=center+z*u;verts.append((x,front(x,z),z))
 for j in range(sides):faces.append((0,1+j,1+(j+1)%sides))
 for r in range(rings-1):
  for j in range(sides):a=1+r*sides+j;b=1+r*sides+(j+1)%sides;faces.append((a,a+sides,b+sides,b))
 return mesh(name,verts,[tuple(reversed(f))for f in faces],material,head)

def surface_disc(name,cx,cz,rx,rz,material,offset=.016,warm=False):
 verts=[(cx,front(cx,cz,offset),cz)];faces=[];rings=8;sides=40
 for r in range(1,rings+1):
  for j in range(sides):
   a=j*math.tau/sides;x=cx+rx*r/rings*math.sin(a);z=cz+rz*r/rings*math.cos(a);verts.append((x,front(x,z,offset),z))
 for j in range(sides):faces.append((0,1+(j+1)%sides,1+j))
 for r in range(rings-1):
  for j in range(sides):a=1+r*sides+j;b=1+r*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
 o=mesh(name,verts,faces,material,head)
 if warm:
  o.shape_key_add(name='Basis');key=o.shape_key_add(name='Warmth')
  for out,v in zip(key.data,o.data.vertices):
   x=cx+(v.co.x-cx)*1.35;z=cz+(v.co.z-cz)*1.25;out.co=(x,front(x,z,offset),z)
 return o

def eye(name,x,z,material,slant=0,lashes=False):
 o=ball(name,(x,front(x,z,.028),z),(.067,.024,.097),material,head)
 if lashes:
  sign=1 if x>0 else -1;parts=[]
  for k in range(2):
   px=x+sign*.046;pz=z+.052+k*.025
   parts.append(tube('Soft stitched eyelash',[(px,front(px,pz,.035),pz),(px+sign*.041,front(px+sign*.041,pz+.03,.035),pz+.03)],.009,material,head))
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
  for part in parts:part.select_set(True)
  bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
 o.shape_key_add(name='Basis')
 for kind in FACE_KEYS:
  key=o.shape_key_add(name=kind)
  for out,v in zip(key.data,o.data.vertices):
   p=v.co.copy();nx=max(-1.1,min(1.1,p.x/.067));p.z+=slant*p.x
   if kind=='Blink':p.z=p.z*.055+.010*(1-min(1,nx*nx))
   elif kind=='SoftSmile':p.z=p.z*.10+.030*(1-min(1,nx*nx));p.x*=1.08
   elif kind=='Sleepy':p.z=p.z*.16-.01;p.x*=1.04
   elif kind=='Surprise':p.z*=1.14;p.x*=1.25
   elif kind=='Shy':p.z=p.z*.75-.012;p.x*=.9
   elif kind=='Curious':p.z*=1.13 if x<0 else .79
   out.co=p
 return o

def mouth_curve(kind,t,wide=False):
 if wide:
  # Cinnamoroll keeps the original embroidered W mouth.
  x=(t-.5)*.25;z=-.030*math.sin(math.pi*t*2)**2
  if kind=='SoftSmile':x*=1.16;z*=1.5
  elif kind=='Sleepy':x*=.6;z*=.35
  elif kind=='Surprise':x=.035*math.cos(t*math.tau);z=.043*math.sin(t*math.tau)-.008
  elif kind=='Shy':x*=.78;z*=.6
  elif kind=='Curious':z+=x*.2
  return x,z
 u=2*t-1;half=.075;depth=.026
 if kind=='SoftSmile':half*=1.12;depth*=1.18
 elif kind=='Sleepy':half*=.78;depth*=.65
 elif kind=='Surprise':return .026*math.cos(t*math.tau),.032*math.sin(t*math.tau)-.008
 elif kind=='Shy':half*=.85;depth*=.72
 x=u*half;z=depth*(u*u-1)
 if kind=='Curious':z+=.003*u
 return x,z

def smile_geometry(kind,z):
 points=[Vector((x,0,z+dz))for x,dz in [mouth_curve(kind,i/32)for i in range(33)]]
 verts=[];faces=[];sides=8
 for i,p in enumerate(points):
  tangent=(points[min(i+1,32)]-points[max(0,i-1)]).normalized();across=Vector((-tangent.z,0,tangent.x))
  t=i/32;cap=1
  if kind!='Surprise':
   end=min(t,1-t)/.10
   if end<1:cap=math.sqrt(max(.0025,1-(1-end)**2))
  r=.006*cap
  for j in range(sides):
   a=j*math.tau/sides;v=p+across*(r*math.cos(a))
   # The back of the thread is embedded slightly in the ivory face patch.
   # Reproject every vertex, so the smile never floats off the curved cheek.
   verts.append((v.x,front(v.x,v.z,.012)-r*(.85+math.sin(a)),v.z))
 for i in range(32):
  for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
 faces.extend([tuple(range(sides-1,-1,-1)),tuple(32*sides+j for j in range(sides))])
 return verts,faces

def mouth(name,z,material,wide=False):
 def make(kind,tempname):
  if not wide:
   verts,faces=smile_geometry(kind,z);return mesh(tempname,verts,faces,material,head if tempname==name else None)
  ps=[]
  for i in range(33):
   x,dz=mouth_curve(kind,i/32,True);ps.append((x,front(x,z+dz,.03),z+dz))
  return tube(tempname,ps,.010,material,head if tempname==name else None)
 o=make('Basis',name);o.shape_key_add(name='Basis')
 for kind in FACE_KEYS[1:]:
  temp=make(kind,'Temporary mouth morph');key=o.shape_key_add(name=kind)
  for out,v in zip(key.data,temp.data.vertices):out.co=v.co
  d=temp.data;bpy.data.objects.remove(temp,do_unlink=True);bpy.data.meshes.remove(d)
 return o

def bow(name,pos,size,material,ctrl):
 x,y,z=pos
 for sign in [-1,1]:
  o=ball(name+' loop '+str(sign),(x+sign*size*.32,y,z+sign*size*.04),(size*.34,size*.12,size*.23),material,ctrl,24,16);o.rotation_euler.y=sign*.20
 ball(name+' knot',(x,y-.035,z),(size*.14,size*.16,size*.14),material,ctrl,24,16)

def area(name,pos,power,size,color,target=(0,0,1.4)):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def studio():
 s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=128;s.render.resolution_x=720;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
 s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.76,.69,.72,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 area('Large warm key',(-3,-4,6),450,4.5,(1,.91,.85));area('Soft cream fill',(4,-2,3.5),280,4,(.88,.93,1));area('Pink rim',(1,3,5),380,3.5,(1,.80,.87))
 ground=mat('Studio blush',(.82,.64,.69));ivory=mat('Studio biscuit',(.89,.80,.72))
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08));o=link(bpy.context.object,stage);o.name='Studio floor';o.data.materials.append(ground)
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.6,depth=.10,location=(0,0,-.04));o=link(bpy.context.object,stage);o.name='Studio plinth';o.data.materials.append(ivory);bevel=o.modifiers.new('Soft edge','BEVEL');bevel.width=.045;bevel.segments=3
 bpy.ops.object.camera_add();o=link(bpy.context.object,stage);o.name='Portrait camera';o.location=(4,-9,4.0);target=Vector((0,0,1.48 if style!='cinnamoroll'else 1.12));o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=4.3 if style!='cinnamoroll'else 4.25;s.camera=o
 for screen in bpy.data.screens:
  for a in screen.areas:
   if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL';a.spaces.active.overlay.show_overlays=False


def key_ctrl(o,frame,rot=(0,0,0),offset=(0,0,0),scale=(1,1,1)):
 o.location=rest[o.name][0]+Vector(offset);o.rotation_euler=rot;o.scale=scale
 for path in ['location','rotation_euler','scale']:o.keyframe_insert(path,frame=frame)

def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def author():
 s=bpy.context.scene
 for label,(first,last)in CLIPS.items():
  s.timeline_markers.new(label,frame=first)
  frames=sorted(set([first,last,*range(first,last+1,3)]))
  for f in frames:
   t=(f-first)/(last-first);a=t*math.tau;eng=smooth(t/.18)*(1-smooth((t-.80)/.20));rots={};offsets={};faces={};left=right=0
   if label=='idle':
    rots['CTRL_Head']=(.015*math.sin(a),0,.015*math.sin(a));left=right=max(0,1-abs(t-.625)/.03125)
   elif label=='wave':
    rots['CTRL_Arm_R']=(-.22*eng,-1.15*eng,.3*math.sin(a*3)*eng)
    rots['CTRL_Head']=(.025*eng,0,-.10*eng)
    if style=='cinnamoroll':rots['CTRL_Arm_L']=(-.22*eng,1.0*eng,-.22*math.sin(a*3)*eng)
    faces['SoftSmile']=.65*eng
    if style=='kuromi':right=eng
   elif label=='dance':
    # Six-second side steps, whole-body sway and two gentle hops, with delayed ears.
    swing=math.sin(a*3)*eng;lift=(max(0,math.sin(a*3))**2)*.075*eng
    offsets['CTRL_Root']=(.18*swing,0,lift);rots['CTRL_Body']=(.035*math.sin(a*6)*eng,0,-.11*swing);rots['CTRL_Head']=(0,.12*math.sin(a*3-.3)*eng,.07*swing)
    for side,sign in [('L',-1),('R',1)]:
     rots['CTRL_Arm_'+side]=(-.2*eng,-sign*(.80+.60*math.sin(a*3+sign*.7))*eng,sign*.1*eng)
     offsets['CTRL_Foot_'+side]=(sign*.10*math.sin(a*3)*eng,0,max(0,math.sin(a*3+sign*math.pi/2))*.06*eng)
    faces['SoftSmile']=eng
   elif label=='bow':
    rots['CTRL_Body']=(.25*eng,0,0);rots['CTRL_Head']=(.13*eng,0,0)
    for side,sign in [('L',-1),('R',1)]:rots['CTRL_Arm_'+side]=(-.32*eng,sign*.2*eng,0)
    left=right=.85*eng
   elif label=='celebrate':
    offsets['CTRL_Root']=(0,0,.12*math.sin(a*2)**2*eng)
    for side,sign in [('L',-1),('R',1)]:rots['CTRL_Arm_'+side]=(-.25*eng,-sign*1.8*eng,sign*.10*math.sin(a*4)*eng)
    faces['SoftSmile']=eng;rots['CTRL_Head']=(-.06*eng,.10*math.sin(a*2)*eng,0)
   elif label=='cuddle':
    for side,sign in [('L',-1),('R',1)]:rots['CTRL_Arm_'+side]=(-1.0*eng,sign*.5*eng,0);offsets['CTRL_Arm_'+side]=(-sign*.13*eng,-.015*eng,0)
    rots['CTRL_Head']=(.10*eng,0,.05*eng);faces['SoftSmile']=eng;faces['Warmth']=eng
   elif label=='walk':
    offsets['CTRL_Root']=(0,0,.025*(1-math.cos(a*4)))
    for side,sign in [('L',-1),('R',1)]:
     phase=a*2+(math.pi if sign>0 else 0);offsets['CTRL_Foot_'+side]=(0,.12*math.cos(phase),.07*max(0,math.sin(phase)));rots['CTRL_Arm_'+side]=(.25*math.cos(phase+math.pi),0,0)
    rots['CTRL_Head']=(.015*math.sin(a*4),0,0)
   else:
    if label=='happy':faces['SoftSmile']=eng
    elif label=='wink':right=eng;faces['SoftSmile']=.25*eng;rots['CTRL_Head']=(0,0,-.09*eng)
    elif label=='sleepy':faces['Sleepy']=eng;rots['CTRL_Head']=(.09*eng,0,.04*eng)
    elif label=='surprised':faces['Surprise']=eng;rots['CTRL_Head']=(-.07*eng,0,0)
    elif label=='shy':faces['Shy']=eng;faces['Warmth']=eng;rots['CTRL_Head']=(.08*eng,.12*eng,-.035*eng)
    elif label=='curious':faces['Curious']=eng;rots['CTRL_Head']=(0,-.08*eng,.16*eng)
   for side,sign in [('L',-1),('R',1)]:
    if label not in ['walk']:
     wave=math.sin(a*(3 if label=='dance'else 1)-.5)*eng
     rots['CTRL_Ear_'+side]=(.04*wave,sign*.065*wave,sign*(.08 if style=='cinnamoroll'else .035)*wave)
   for o in animated:
    key_ctrl(o,f,rots.get(o.name,(0,0,0)),offsets.get(o.name,(0,0,0)),(1,1,1+.008*math.sin(a))if o==body and label=='idle'else(1,1,1))
   for o in morphs:
    for k in o.data.shape_keys.key_blocks:
     if k.name=='Basis':continue
     blink=left if o.name=='Eye left'else right
     k.value=blink if k.name=='Blink'else faces.get(k.name,0)*(1-blink if o.name.startswith('Eye ')else 1)
     k.keyframe_insert('value',frame=f)
 for o in [*animated,*[o.data.shape_keys for o in morphs]]:
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    for p in fc.keyframe_points:p.handle_left_type='AUTO_CLAMPED';p.handle_right_type='AUTO_CLAMPED'
 s.frame_start=1;s.frame_end=1441;s.render.fps=FPS;s.frame_set(1)
 s['friend_character']=style;s['friend_title']=TITLES[style];s['friend_clips']=json.dumps(CLIPS);s['friend_version']='little-friends-v1'
 if style!='cinnamoroll':s['friend_mouth_version']='soft-stitched-smile-v2'
 s['help']='Open START HERE text. Timeline markers name each gesture/expression. Pose the CTRL_ empties. Eyes/mouth have editable shape keys. No held item by default.'
 text=bpy.data.texts.new('START HERE — '+TITLES[style]);text.write('''EDITABLE LITTLE FRIEND\n\nSpace plays the timeline. Jump to the frame ranges below to preview each motion.\nCTRL_Root moves the whole character; Body/Head/Arms/Feet/Ears pose the parts.\nEye left, Eye right and Embroidered smile expose real facial shape keys in Object Data.\nPink cheek meshes have the Warmth morph. Reset values at frame 1 for a neutral pose.\nThe STUDIO collection is separate from character export. F12 renders the lit portrait.\nRun export_friends.py to export your edited file without recreating it.\n\n'''+ '\n'.join(f'{name}: {a}–{b} at 24fps'for name,(a,b)in CLIPS.items()))


def build(which):
 global style,char,rig,stage,head_scale,head_z,root,body,head,animated,rest,morphs
 style=which;bpy.ops.wm.read_factory_settings(use_empty=False);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for col in list(bpy.data.collections):bpy.data.collections.remove(col)
 char=bpy.data.collections.new('CHARACTER — '+TITLES[style]);rig=bpy.data.collections.new('CONTROLS — pose these');stage=bpy.data.collections.new('STUDIO — not exported')
 for col in [char,rig,stage]:bpy.context.scene.collection.children.link(col)
 cream=mat('Warm ivory plush',(.94,.91,.84));pink=mat('Melody rose plush',(.80,.25,.43));ribbon=mat('Rose ribbon plush',(.70,.12,.30));pale=mat('Blush embroidery',(.97,.63,.70));dark=mat('Soft cocoa stitching',(.055,.030,.040),False);charcoal=mat('Kuromi charcoal plush',(.035,.031,.045));yellow=mat('Butter yellow nose',(.98,.72,.13),False);blue=mat('Cinnamon sky embroidery',(.018,.32,.56),False)
 root=control('CTRL_Root',(0,0,0));body=control('CTRL_Body',(0,0,.66),root)
 head_z=1.68 if style=='cinnamoroll'else 1.80;head_scale=(.91,.48,.56)if style=='cinnamoroll'else(.81,.53,.67)
 head=control('CTRL_Head',(0,0,head_z),body)
 for side,sign in [('L',-1),('R',1)]:
  arm=control('CTRL_Arm_'+side,(sign*.40,0,1.10),body);ball('Relaxed paw '+side,(sign*.48,-.018,.84),(.18,.21,.30),cream,arm)
  foot=control('CTRL_Foot_'+side,(sign*.26,-.18,.23),root);ball('Foot '+side,(sign*.26,-.20,.23),(.255,.32,.23),cream,foot)
  if style=='melody':
   ball('Little paw pad '+side,(sign*.26,-.511,.20),(.072,.014,.060),pale,foot,24,16)
   for dx,dz in [(-.060,.29),(0,.315),(.060,.29)]:ball('Toe bean '+side,(sign*.26+dx,-.499,dz),(.026,.014,.028),pale,foot,20,12)
 ball('Plush body',(0,.015,.66),(.44,.34,.52),cream,body)
 ball('Head',(0,0,head_z),head_scale,cream if style=='cinnamoroll'else pink if style=='melody'else charcoal,head,64,40)
 if style!='cinnamoroll':face_patch('Ivory face opening',1.64,.63,.42,cream,.14 if style=='kuromi'else 0)
 for side,sign in [('L',-1),('R',1)]:
  ctrl=control('CTRL_Ear_'+side,(sign*.55,.025,2.22 if style!='cinnamoroll'else 1.90),head)
  if style=='cinnamoroll':
   path=[(sign*.65,.04,1.86),(sign*.98,.025,1.75),(sign*1.22,0,1.48),(sign*1.36,-.025,1.23),(sign*1.42,-.04,1.11)]
   ear('Long floppy ear '+side,path,[.16,.24,.24,.18,.001],[.11,.14,.13,.11,.001],cream,ctrl)
  elif style=='melody':
   path=[(sign*.48,.02,2.24),(sign*.61,.02,2.56),(sign*.66,.03,2.87),(sign*.55,.02,3.12)]if sign<0 else[(.48,.02,2.24),(.61,.02,2.56),(.66,0,2.83),(.51,-.08,3.0)]
   ear('Soft hood ear '+side,path,[.19,.23,.21,.001]if sign<0 else[.19,.24,.22,.001],[.13,.13,.12,.001],pink,ctrl)
  else:
   path=[(sign*.47,.03,2.26),(sign*.65,.025,2.46),(sign*.84,.02,2.70),(sign*.99,.01,2.94)]
   ear('Jester ear '+side,path,[.23,.28,.19,.025],[.12,.13,.11,.025],charcoal,ctrl);ball('Jester pom '+side,(sign*.99,.01,2.95),(.10,.10,.10),charcoal,ctrl,24,16)
 for side,sign in [('left',-1),('right',1)]:eye('Eye '+side,sign*.26,1.69 if style!='cinnamoroll'else 1.65,blue if style=='cinnamoroll'else dark,slant=sign*.2 if style=='kuromi'else 0,lashes=style=='kuromi')
 if style!='cinnamoroll':ball('Button nose',(0,front(0,1.56,.035),1.56),(.052,.039,.040),pink if style=='kuromi'else yellow,head,24,16)
 stitch=mat('Soft mouth embroidery',(.055,.030,.040));p=stitch.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85;p.inputs['Sheen Weight'].default_value=0;p.inputs['Specular IOR Level'].default_value=.12
 mouth('Embroidered smile',1.47 if style!='cinnamoroll'else 1.46,blue if style=='cinnamoroll'else stitch,style=='cinnamoroll')
 for sign in [-1,1]:surface_disc('Pink cheek '+str(sign),sign*.40,1.51,.09,.035,pale,warm=True)
 if style=='melody':
  bow('Hood bow',(-.42,-.37,2.54),.55,ribbon,head);bow('Neck ribbon',(0,-.31,1.17),.35,ribbon,body)
  for sign in [-1,1]:
   verts=[(sign*.03,-.325,1.15),(sign*.12,-.35,1.10),(sign*.18,-.36,.91),(sign*.08,-.37,.96)];r=mesh('Ribbon tail '+str(sign),verts,[(0,1,2,3)],pink,body);sol=r.modifiers.new('Soft ribbon thickness','SOLIDIFY');sol.thickness=.015;be=r.modifiers.new('Rounded ribbon edge','BEVEL');be.width=.012;be.segments=3
 elif style=='cinnamoroll':
  tail=control('CTRL_Tail',(0,.32,.60),body);pts=[]
  for i in range(81):
   t=i/80;a=t*math.tau*1.20;r=.27*(1-t)+.035;pts.append((r*math.sin(a),.37,r*math.cos(a)+.59))
  tube('Cinnamon roll tail',pts,.085,cream,tail);ball('Rounded tail end',pts[-1],(.085,.085,.085),cream,tail,24,16)
 else:
  collar=ball('Jester collar',(0,0,1.17),(.42,.30,.115),charcoal,body,32,16)
  for sign in [-1,1]:ball('Collar pom '+str(sign),(sign*.28,-.255,1.09),(.085,.08,.085),pink,body,24,16)
  surface_disc('Pink skull badge',0,2.23,.154,.122,pale,.019)
  for sign in [-1,1]:surface_disc('Skull eye '+str(sign),sign*.060,2.24,.026,.039,charcoal,.023)
  for x in [-.042,0,.042]:surface_disc('Skull tooth',x,2.10,.014,.032,pale,.019)
  surface_disc('Skull nose',0,2.205,.009,.012,charcoal,.024)
 for obj in char.objects:
  if obj.modifiers:
   bpy.context.view_layer.objects.active=obj
   for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
 bpy.ops.object.select_all(action='DESELECT')
 for obj in char.objects:
  if obj.type=='MESH':obj.select_set(True)
 bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
 animated=[o for o in rig.objects if o.name.startswith('CTRL_')];rest={o.name:(o.location.copy(),o.rotation_euler.copy())for o in animated};morphs=[o for o in char.objects if o.type=='MESH'and o.data.shape_keys]
 author();studio();s=bpy.context.scene;s.render.filepath='//'+style+'.png';bpy.context.preferences.filepaths.save_version=0
 bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
 for area in bpy.context.screen.areas:
  if area.type=='DOPESHEET_EDITOR':
   region=next((r for r in area.regions if r.type=='WINDOW'),None)
   if region:
    with bpy.context.temp_override(area=area,region=region):bpy.ops.action.view_all()
 path=OUT/(style+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path));print('FRIEND_SOURCE_READY',style,len(char.objects),'parts',flush=True)
 if '--render'in sys.argv:bpy.ops.render.render(write_still=True)

if __name__=='__main__':
 choices=[sys.argv[sys.argv.index('--character')+1]]if'--character'in sys.argv else list(TITLES)
 for which in choices:build(which)
