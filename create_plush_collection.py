"""Create all five editable, animated plush editions before exporting to the game.
blender -b --python-exit-code 1 --python create_plush_collection.py
No hair add-on or external texture is required. Existing source files are preserved.
"""
import bpy, math, json, random, bisect, sys
from pathlib import Path
from mathutils import Vector, Matrix
OUT=Path(__file__).resolve().parent
BASE=OUT/'hello_kitty_natural.blend'
STYLES=[('cloud','Strawberry Cloud',(.92,.055,.25)),('witch','Moonlight Witch',(.69,.15,.39)),('baby','Baby Blossom',(.91,.39,.59)),('kitten','Rose Kitten',(.96,.93,.89)),('bunny','Silver Bunny',(.93,.90,.83))]

def material(name,color,metal=0,fabric=True):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
 bs.inputs['Roughness'].default_value=.88 if fabric else .4;bs.inputs['Metallic'].default_value=metal
 bs.inputs['Specular IOR Level'].default_value=.18 if fabric else .35
 if fabric:
  bs.inputs['Sheen Weight'].default_value=.25;bs.inputs['Sheen Roughness'].default_value=.8
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=cloth
  normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.28
  m.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 return m

def uv(o):
 if o.type!='MESH':return
 layer=o.data.uv_layers.active or o.data.uv_layers.new(name='Plush fabric UV')
 center=sum((Vector(c)for c in o.bound_box),Vector())/8
 for loop in o.data.loops:
  p=o.data.vertices[loop.vertex_index].co-center;r=max(.0001,p.length)
  layer.data[loop.index].uv=(8*(.5+math.atan2(p.y,p.x)/math.tau),8*(.5+math.asin(max(-1,min(1,p.z/r)))/math.pi))

def relink(o,name,mat,parent=None):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 char.objects.link(o);o.data.materials.clear();o.data.materials.append(mat)
 if parent:
  world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
  uv(o)
 return o

def ball(name,pos,scale,mat,parent=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos)
 o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return relink(o,name,mat,parent or body)

def line(name,points,r,mat,parent=None,cyclic=False):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2;d.resolution_u=8
 sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1);sp.use_cyclic_u=cyclic
 for v,p in zip(sp.bezier_points,points):v.co=p;v.handle_left_type='AUTO';v.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);char.objects.link(o);d.materials.append(mat)
 if parent:
  bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
 return o

def control(name,pos,parent):
 o=bpy.data.objects.new(name,None);controls.objects.link(o);o.empty_display_type='CIRCLE';o.empty_display_size=.18
 o.location=pos;bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
 return o

# Twelve-vertex curled fibers share a single merged surface per body part. No
# thousands of Object3Ds, alpha-card fur or unsupported particle export.
def pile(target,count,size,mat,mask_face=False):
 d=target.data;d.calc_loop_triangles();tris=list(d.loop_triangles);weights=[];total=0
 for t in tris:total+=t.area;weights.append(total)
 verts=[];faces=[];origins=[];samples=[]
 rng=random.Random(420+sum(map(ord,target.name)))
 for _ in range(count):
  t=tris[min(len(tris)-1,bisect.bisect_left(weights,rng.random()*total))];a,b,c=[d.vertices[i]for i in t.vertices]
  q=math.sqrt(rng.random());v=rng.random();w=(1-q,q*(1-v),q*v)
  p=a.co*w[0]+b.co*w[1]+c.co*w[2];normal=(a.normal*w[0]+b.normal*w[1]+c.normal*w[2]).normalized()
  world=target.matrix_world@p
  if mask_face and world.y<-.48 and abs(world.x)<1.15 and 2.78<world.z<3.7:continue
  radius=size*rng.uniform(.65,1.22)
  axis=Vector((0,0,1)).rotation_difference(normal)
  start=len(verts)
  # A fine tapered, gently curled strand, with three vertices per cross section.
  # The curls create a soft silhouette instead of a surface of spherical beads.
  for k in range(4):
   phase=k/3;center=Vector((radius*.8*phase*phase,radius*.18*math.sin(phase*math.pi),radius*(.05+.9*math.sin(phase*math.pi*.72))))
   thickness=radius*.055*(1-.75*phase)
   for j in range(3):
    angle=j*math.tau/3
    verts.append(p+axis@(center+Vector((math.cos(angle)*thickness,math.sin(angle)*thickness,0))))
  for k in range(3):
   for j in range(3):
    a=start+k*3+j;b=start+k*3+(j+1)%3;c=start+(k+1)*3+(j+1)%3;d2=start+(k+1)*3+j
    faces.extend([(a,b,c),(a,c,d2)])
  samples.append((t.vertices,w,start))
 mesh=bpy.data.meshes.new('Short curled pile '+target.name);mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('Plush pile '+target.name,mesh);char.objects.link(o);o.parent=target;o.location=(0,0,0);o['plush_fur']=True
 mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=True
 uv(o)
 if d.shape_keys:
  o.shape_key_add(name='Basis')
  for key in d.shape_keys.key_blocks:
   if key.name=='Basis':continue
   k=o.shape_key_add(name=key.name)
   for ids,w,start in samples:
    delta=sum(((key.data[i].co-d.vertices[i].co)*q for i,q in zip(ids,w)),Vector())
    for j in range(12):k.data[start+j].co+=delta
  if d.shape_keys.animation_data and d.shape_keys.animation_data.action:
   mesh.shape_keys.animation_data_create();mesh.shape_keys.animation_data.action=d.shape_keys.animation_data.action.copy()
 return o

def bow(name,pos,size,mat,parent):
 x,y,z=pos;parts=[]
 for sign in [-1,1]:
  o=ball(name+' loop '+str(sign),(x+sign*size*.38,y,z+sign*size*.05),(size*.42,size*.19,size*.32),mat,parent);o.rotation_euler.y=sign*.22;parts.append(o)
 parts.append(ball(name+' knot',(x,y-.055,z),(size*.22,size*.22,size*.23),mat,parent))
 return parts

def join_eye(eye,parts):
 bpy.ops.object.select_all(action='DESELECT');eye.select_set(True)
 for o in parts:
  o.select_set(True);bpy.context.view_layer.objects.active=o
  if o.type=='CURVE':bpy.ops.object.convert(target='MESH')
 bpy.context.view_layer.objects.active=eye;bpy.ops.object.join()

for style,title,color in STYLES:
 if '--style' in sys.argv and sys.argv[sys.argv.index('--style')+1]!=style:continue
 bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene;s.frame_set(1)
 char=bpy.data.collections['HELLO KITTY — editable parts'];controls=bpy.data.collections['ANIMATION — select controls to pose']
 head=bpy.data.objects['CTRL_Head'];body=bpy.data.objects['CTRL_Body'];root=bpy.data.objects['CTRL_Root']
 # Self-contained fine knitted normal map, shared by all fabric materials.
 cloth=bpy.data.images.new('Packed plush fiber normal',width=128,height=128);cloth.colorspace_settings.name='Non-Color'
 pixels=[]
 for y in range(128):
  for x in range(128):
   u=x/128;v=y/128;a=math.tau*(18*u+1.3*math.sin(math.tau*12*v));b=math.tau*(16*v+.6*math.sin(math.tau*14*u))
   n=Vector((.25*math.cos(a)+.12*math.sin(b),.25*math.cos(b)+.08*math.sin(a),1)).normalized();pixels.extend((n.x*.5+.5,n.y*.5+.5,n.z*.5+.5,1))
 cloth.pixels=pixels;cloth.pack()
 cream=material('Plush warm cream',(.96,.925,.855));rose=material('Plush rose fabric',color)
 blush=material('Plush blush',(.98,.58,.66));lavender=material('Plush lilac felt',(.56,.35,.72));yellow=material('Plush butter embroidery',(.98,.78,.24));silver=material('Plush silver satin',(.66,.72,.8),.65,False)
 brown=material('Plush cocoa embroidery',(.075,.025,.022),0,False);brown.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
 for o in list(char.objects):
  if o.type=='MESH':
   mats=[m.name for m in o.data.materials]
   if 'Warm porcelain white' in mats:o.data.materials.clear();o.data.materials.append(cream);uv(o)
   elif 'Strawberry pink satin' in mats or 'Ribbon fold rose' in mats:o.data.materials.clear();o.data.materials.append(rose);uv(o)
  if o.name.startswith(('Eye','Whisker','Wink')):
   o.data.materials.clear();o.data.materials.append(brown)
   if o.type=='CURVE' and o.name.startswith('Whisker'):o.data.bevel_depth=.021
 # Reserve name-based wardrobe contracts for all five editions.
 bpy.data.materials['Strawberry pink satin'].name='Original satin — preserved'
 rose.name='Strawberry pink satin';cream.name='Plush cream fabric'
 fabric_targets=[(bpy.data.objects['Head'],3500,.052,cream,True)]
 for sign in [-1,1]:
  fabric_targets.extend([(bpy.data.objects['Foot '+str(sign)],350,.048,cream,False),(bpy.data.objects['White arm '+str(sign)],350,.04,cream,False)])
 for o in list(char.objects):
  if o.name.startswith('Bow loop') or o.name=='Bow center knot':fabric_targets.append((o,180,.03,rose,False))
 # Round the original ear tips with stuffed cap volume.
 for sign in ([-1,1] if style!='bunny' else []):
  cap=ball('Plush rounded ear '+str(sign),(sign*1.18,.02,4.5),(.30,.35,.34),cream,head);fabric_targets.append((cap,180,.04,cream,False))
 if style=='bunny':
  core=bpy.data.objects['Head'];world=core.matrix_world.copy();inverse=world.inverted()
  for vertex in core.data.vertices:
   p=world@vertex.co
   q=Vector((p.x/1.55,p.y/1.04,(p.z-3.4)/1.16))
   if p.z>4.0 and q.length>1:
    q.normalize();p=Vector((q.x*1.55,q.y*1.04,3.4+q.z*1.16));vertex.co=inverse@p
 extras=[]
 if style=='cloud':
  for sign in [-1,1]:ball('Cloud collar '+str(sign),(sign*.20,-.46,2.23),(.27,.12,.16),cream,body)
  fabric_targets.append((bpy.data.objects['Strawberry pink rounded dress'],800,.025,rose,False))
 if style=='witch':
  hat=control('CTRL_Plush_Hat',(0,0,4.30),head);extras.append(hat)
  # Bent, softly stuffed cone made of rounded elliptical rings.
  rings=[(4.27,0,0,1.52),(4.52,0,0,1.25),(4.87,.02,.02,.98),(5.24,.10,.03,.72),(5.58,.22,.04,.48),(5.87,.36,.05,.27),(6.03,.56,.07,.10),(6.02,.70,.08,.012)]
  vv=[];ff=[]
  for z,x,y,r in rings:
   vv.extend((x+math.cos(j*math.tau/48)*r,y+math.sin(j*math.tau/48)*r*.67,z)for j in range(48))
  for k in range(len(rings)-1):
   for j in range(48):a=k*48+j;b=k*48+(j+1)%48;ff.append((a,b,b+48,a+48))
  me=bpy.data.meshes.new('Bent padded witch hat');me.from_pydata(vv,[],ff);me.update();o=bpy.data.objects.new('Plush witch hat',me);char.objects.link(o);me.materials.append(lavender)
  bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=hat;o.matrix_world=world;uv(o)
  for f in me.polygons:f.use_smooth=True
  brim=ball('Witch padded brim',(0,0,4.31),(1.62,1.05,.14),lavender,hat);fabric_targets.append((brim,260,.025,lavender,False))
  band=line('Witch lemon ribbon',[(1.37*math.cos(j*math.tau/16),.87*math.sin(j*math.tau/16),4.51)for j in range(16)],.075,yellow,hat,True)
  bow('Witch pink hat bow',(.73,-.88,4.54),.73,rose,hat)
  # A friendly stitched star and a little spider, following the reference hat.
  star=[]
  for j in range(10):a=j*math.pi/5;r=.18 if j%2==0 else .08;star.append((-.38+math.sin(a)*r,-.70,5.00+math.cos(a)*r))
  line('Witch embroidered star',star,.018,yellow,hat,True)
  ball('Witch tiny spider',(.45,-.62,5.12),(.10,.035,.13),brown,hat)
  for sign in [-1,1]:
   for k in [-1,0,1]:line('Witch spider stitch',[(.45+sign*.07,-.64,5.10+k*.05),(.45+sign*.19,-.62,5.15+k*.07),(.45+sign*.23,-.61,5.09+k*.09)],.011,brown,hat)
  # An open-front cape keeps the paws and bouquet free.
  for sign in [-1,1]:
   cape=ball('Witch velvet cape '+str(sign),(sign*.62,.34,1.68),(.65,.44,.84),lavender,body)
  ball('Witch cape clasp',(0,-.52,2.16),(.105,.06,.10),yellow,body)
 if style=='baby':
  dress=bpy.data.objects['Strawberry pink rounded dress']
  for v in dress.data.vertices:
   if v.co.z<1.55:v.co.x*=.80;v.co.y*=.88
  for sign in [-1,1]:
   cuff=ball('Baby romper cuff '+str(sign),(sign*.43,-.08,.90),(.44,.51,.26),rose,body);fabric_targets.append((cuff,90,.03,rose,False))
  bib=ball('Baby lilac bib',(0,-.69,1.98),(.58,.10,.46),lavender,body)
  for j in range(13):
   a=math.pi+(j/12)*math.pi;ball('Baby bib lace '+str(j),(.58*math.cos(a),-.73,1.98+.46*math.sin(a)),(.075,.055,.085),cream,body)
  ball('Baby embroidered duck body',(0,-.805,1.93),(.18,.025,.12),yellow,body);ball('Baby embroidered duck head',(-.09,-.805,2.07),(.09,.026,.095),yellow,body)
  ball('Baby duck eye',(-.11,-.835,2.10),(.015,.008,.018),brown,body);ball('Baby duck beak',(-.19,-.82,2.05),(.05,.025,.025),rose,body)
  ball('Baby pacifier shield',(0,-1.01,2.77),(.25,.07,.14),rose,head)
  line('Baby pacifier ring',[(.105*math.cos(j*math.tau/16),-1.12,2.71+.11*math.sin(j*math.tau/16))for j in range(16)],.028,rose,head,True)
  for sign in [-1,1]:ball('Baby rosy cheek '+str(sign),(sign*.86,-.90,3.0),(.18,.035,.075),blush,head)
 if style in ['kitten','bunny']:
  # Open-faced hood: cut out the front and keep the actual rigged face visible.
  hood=ball('Plush '+style+' hood',(0,.02,3.44),(1.67,1.15,1.28),cream,head)
  import bmesh
  bm=bmesh.new();bm.from_mesh(hood.data)
  remove=[]
  for f in bm.faces:
   p=f.calc_center_median();world=hood.matrix_world@p
   if world.y<-.25 and (world.x/1.48)**2+((world.z-3.38)/1.10)**2<1:remove.append(f)
  bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(hood.data);bm.free()
  fabric_targets.append((hood,1300,.063,cream,False))
  for sign in [-1,1]:
   if style=='bunny':
    ear=control('CTRL_Plush_Ear_'+str(sign),(sign*.65,.02,4.42),head);extras.append(ear)
    e=ball('Bunny long ear '+str(sign),(sign*.65,.04,5.05),(.36,.29,.87),cream,ear);fabric_targets.append((e,380,.07,cream,False))
    ball('Bunny silver inner ear '+str(sign),(sign*.65,-.22,5.10),(.21,.055,.59),silver,ear)
   else:
    ball('Kitten pink inner ear '+str(sign),(sign*1.21,-.30,4.49),(.20,.06,.24),blush,head)
  neck=ball('Plush neck ruff',(0,-.03,2.19),(.79,.64,.23),blush if style=='kitten'else cream,body);fabric_targets.append((neck,900,.055,blush if style=='kitten'else cream,False))
  fabric_targets.append((bpy.data.objects['Strawberry pink rounded dress'],1000,.045,rose,False))
  if style=='kitten':
   for o in list(char.objects):
    if o.name.startswith('Bow'):o.data.materials.clear();o.data.materials.append(blush)
   fabric_targets=[(o,n,length,blush if o.name.startswith('Bow')else mat,mask)for o,n,length,mat,mask in fabric_targets]
   bow('Kitten back bow',(0,.89,1.92),1.13,blush,body)
   for eye_name in ['Eye left','Eye right']:
    eye=bpy.data.objects[eye_name];sign=-1 if eye_name.endswith('left')else 1;cx=sign*.63
    pieces=[ball('Kitten eye sparkle',(cx-.03,-.99,3.33),(.033,.013,.038),cream,head),ball('Kitten eye little sparkle',(cx+.033,-.987,3.24),(.018,.012,.018),blush,head)]
    # A tiny embroidered heart-shaped glint, part of the same winkable eye mesh.
    points=[(cx+.035*math.sin(t)**3,-.995,3.28+.035*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16)for t in [j*math.tau/32 for j in range(32)]]
    pieces.append(line('Kitten heart eye',points,.009,blush,head,True));join_eye(eye,pieces)
   for sign in [-1,1]:ball('Kitten blush '+str(sign),(sign*.88,-.89,3.0),(.14,.025,.065),blush,head)
  else:
   bow('Bunny neck silver bow',(0,-.64,2.10),.75,silver,body)
   for o in list(char.objects):
    if o.name.startswith('Bow'):o.data.materials.clear();o.data.materials.append(silver)
   for sign in [-1,1]:
    eye=bpy.data.objects['Eye left'if sign<0 else'Eye right']
    ring=line('Bunny silver eye seam',[(sign*.63+.13*math.cos(j*math.tau/32),-.975,3.27+.18*math.sin(j*math.tau/32))for j in range(32)],.013,silver,head,True);join_eye(eye,[ring])
 # Build pile last so the tuft meshes use the same deforming arm topology.
 bpy.context.view_layer.update()
 for target,n,length,mat,mask in fabric_targets:pile(target,n,length,mat,mask)
 # An actual second closed-eye arc for a happy expression, separate from wink.
 joy=line('Plush happy left eye',[(-.63-.145*math.cos(j*math.pi/8),-.985,3.23+.085*math.sin(j*math.pi/8))for j in range(9)],.034,brown,head)
 joy['plush_joy_arc']=True
 for f,hidden in [(1,True),(400,True),(406,False),(420,False),(426,True),(727,True)]:
  joy.hide_render=hidden;joy.hide_viewport=hidden;joy.keyframe_insert('hide_render',frame=f);joy.keyframe_insert('hide_viewport',frame=f)
 # Match the Blender viewport expression to the exported happy-eye morphs.
 for eye_name in ['Eye left','Eye right']:
  eye=bpy.data.objects[eye_name]
  for f,closed in [(400,False),(406,True),(420,True),(426,False),(727,False)]:
   eye.hide_render=closed;eye.hide_viewport=closed;eye.keyframe_insert('hide_render',frame=f);eye.keyframe_insert('hide_viewport',frame=f)
 wink=bpy.data.objects['Wink — closed eye']
 for f,closed in [(400,False),(406,True),(420,True),(426,False),(727,False)]:
  wink.hide_render=not closed;wink.hide_viewport=not closed;wink.keyframe_insert('hide_render',frame=f);wink.keyframe_insert('hide_viewport',frame=f)
 # Bespoke soft dance on the established controls; no detached paw translations.
 names=['CTRL_Root','CTRL_Body','CTRL_Head','CTRL_Arm_L','CTRL_Arm_R','CTRL_Foot_L','CTRL_Foot_R']
 s.frame_set(1);rests={n:bpy.data.objects[n].location.copy()for n in names}
 intensity={'cloud':1,'witch':.8,'baby':.55,'kitten':.85,'bunny':.7}[style]
 for f in range(1,50,2):
  t=(f-1)/48;envelope=math.sin(t*math.pi)**2;sway=math.sin(t*math.tau)*envelope;bounce=(1-math.cos(t*math.tau*2))*.025*envelope*intensity
  for n in names:
   o=bpy.data.objects[n];o.location=rests[n];o.rotation_euler=(0,0,0);o.scale=(1,1,1)
  root.location=rests['CTRL_Root']+Vector((sway*.06,0,bounce));root.rotation_euler.z=sway*(.18 if style=='witch'else .08)
  bpy.data.objects['CTRL_Body'].rotation_euler.y=sway*.035
  head.rotation_euler=(.025*envelope,-.08*sway,.025*sway)
  for sign,side in [(-1,'L'),(1,'R')]:
   arm=bpy.data.objects['CTRL_Arm_'+side];arm.rotation_euler=( -.08*envelope, sign*.27*envelope*intensity + .10*sway,0)
   foot=bpy.data.objects['CTRL_Foot_'+side];foot.location=rests[foot.name]+Vector((0,0,max(0,sign*sway)*.035*intensity))
  for n in names:
   for prop in ['location','rotation_euler','scale']:bpy.data.objects[n].keyframe_insert(prop,frame=f)
  for o in extras:
   o.rotation_euler=(.035*sway,.07*math.sin(t*math.tau*2)*envelope,.025*sway)
   o.keyframe_insert('rotation_euler',frame=f)
 for o in extras:
  o.rotation_euler=(0,0,0);o.keyframe_insert('rotation_euler',frame=50);o.keyframe_insert('rotation_euler',frame=727)
 for o in controls.objects:
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    for k in fc.keyframe_points:k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
 s['plush_variant']=style;s['plush_title']=title;s['plush_body_height']=4.56808
 s['plush_guide']='13 named motions; short merged curled pile, packed fabric normal map, deforming elbow/paw pile. Dance: 1–49. Wave/wink: 49–97. Happy: 391–451. Original file preserved.'
 for o in char.objects:
  ancestor=o.parent
  while ancestor and ancestor.name!='CTRL_Bouquet':ancestor=ancestor.parent
  if ancestor:o.animation_data_clear();o.hide_render=True;o.hide_viewport=True
 for coll in bpy.data.collections:
  if coll.name.startswith('GAME'):
   for o in coll.objects:o.hide_render=True
 # A clean fabric portrait, with room around the witch hat and bunny ears.
 s.camera.location=(2.8,-15,6.2);target=Vector((0,-.05,2.80 if style in ['witch','bunny']else 2.45));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=7.1 if style in ['witch','bunny']else 6.2
 s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=48;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath='//hello_kitty_plush_'+style+'.png'
 s.frame_set(1);bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('hello_kitty_plush_'+style+'.blend')))
 if '--render' in sys.argv:bpy.ops.render.render(write_still=True)
 print('PLUSH_EDITION_READY',style,flush=True)
print('ALL_FIVE_PLUSH_BLENDERS_READY',flush=True)
