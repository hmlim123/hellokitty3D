"""Author game performances, hand sockets, friends and matching toy props.
blender -b hello_kitty_animated.blend --python-exit-code 1 --python create_game_assets.py
Creates hello_kitty_game.blend; preserves both original source files.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
s=bpy.context.scene
if bpy.data.objects.get('Socket_Paw_L'):raise RuntimeError('Open hello_kitty_animated.blend to rebuild.')
s.frame_set(1)
controls=bpy.data.collections['ANIMATION — select controls to pose']
base={o.name:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in controls.objects}
def empty(name,coll,parent=None,world=None):
    o=bpy.data.objects.new(name,None);coll.objects.link(o);o.empty_display_type='SPHERE';o.empty_display_size=.09
    if parent:o.parent=parent
    if world:
        bpy.context.view_layer.update();o.location=parent.matrix_world.inverted()@Vector(world) if parent else world
    return o
for side,x in [('L',-.59),('R',.59)]:
    empty('Socket_Paw_'+side,controls,bpy.data.objects['CTRL_Arm_'+side],(x,-.99,1.84))
mid=empty('Grip_Midpoint',controls,bpy.data.objects['CTRL_Body'])
for side,influence in [('L',1),('R',.5)]:
    c=mid.constraints.new('COPY_LOCATION');c.target=bpy.data.objects['Socket_Paw_'+side];c.influence=influence
tray=empty('Socket_Tray',controls,mid);tray.location=(0,0,-.23)
cup=empty('Socket_Teacup',controls,bpy.data.objects['Socket_Paw_R']);cup.location=(-.12,-.04,-.1)
clips={'dance':[1,49],'wave':[49,97],'offer':[97,140], 'stir':[145,217], 'cut':[217,265], 'present':[265,313], 'surprise':[313,349], 'bow':[349,391], 'celebrate':[391,451], 'sip':[451,511]}
def pose(name,f,off=(0,0,0),rot=(0,0,0)):
    o=bpy.data.objects[name];loc,_,scale=base[name];o.location=loc+Vector(off);o.rotation_euler=rot;o.scale=scale
    for p in ('location','rotation_euler','scale'):o.keyframe_insert(p,frame=f)
# Every clip starts and finishes at the same neutral toy pose. Shoulder pivots
# remain stable: paw movement is authored on these controls, not detached meshes.
for name,(start,end) in list(clips.items())[3:]:
    for f in range(start,end+1,3):
        t=(f-start)/(end-start);p=math.sin(math.pi*t)**2
        for ctrl in base:pose(ctrl,f)
        if name=='stir':
            a=t*math.pi*6;pose('CTRL_Arm_R',f,rot=(.14*math.cos(a)*p,.14*math.sin(a)*p,-.06*p))
            pose('CTRL_Arm_L',f,rot=(.07*p,0,0));pose('CTRL_Head',f,rot=(.08*p,-.06*p,0))
        elif name=='cut':
            press=math.sin(t*math.pi*2)**2*p;pose('CTRL_Arm_R',f,rot=(.30*press,0,0));pose('CTRL_Head',f,rot=(.1*p,0,0))
        elif name=='present':
            for side in ('L','R'):pose('CTRL_Arm_'+side,f,rot=(-.42*p,0,0))
            pose('CTRL_Head',f,rot=(0,-.07*p,0))
        elif name=='surprise':
            pose('CTRL_Head',f,(0,0,.04*p),(-.07*p,-.16*p,0))
            for side,sign in [('L',-1),('R',1)]:pose('CTRL_Arm_'+side,f,rot=(0,sign*.12*p,0))
        elif name=='bow':
            pose('CTRL_Body',f,(0,-.02*p,0),(.13*p,0,0));pose('CTRL_Head',f,rot=(.12*p,0,0))
        elif name=='celebrate':
            lift=abs(math.sin(t*math.pi*3))*.08*p;pose('CTRL_Root',f,(0,0,lift),(0,.055*math.sin(t*math.pi*4)*p,0))
            for side,sign in [('L',-1),('R',1)]:pose('CTRL_Arm_'+side,f,rot=(0,sign*.8*p,0))
            pose('CTRL_Head',f,rot=(0,.07*math.sin(t*math.pi*3)*p,0))
        elif name=='sip':
            pose('CTRL_Arm_R',f,rot=(-.95*p,0,0));pose('CTRL_Head',f,rot=(.05*p,0,0))
    for ctrl in base:pose(ctrl,end)
    s.timeline_markers.new(name.title(),frame=start)
for o in controls.objects:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='BEZIER'
s['kitty_clips']=json.dumps(clips)
s['Game authoring guide']='Named timeline performances at 24fps. CTRL_* are rigid toy controls. Socket_Paw_L/R, Socket_Teacup and Socket_Tray are prop anchors. Exporter turns ranges into separate named glTF clips; originals remain untouched.'
# A matching low-poly rounded toy set; each assembly uses its own root.
props=bpy.data.collections.new('GAME — cozy props');s.collection.children.link(props)
friends=bpy.data.collections.new('GAME — friends');s.collection.children.link(friends)
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.68
    return m
rose=material('Game rose porcelain',(.82,.41,.56));cream=material('Game warm cream',(.94,.84,.69));honey=material('Game teddy honey',(.59,.35,.19));ink=material('Game soft ink',(.055,.027,.036));mint=material('Game sage',(.46,.64,.48));white=material('Game bunny cream',(.92,.83,.74));tea=material('Game tea',(.38,.20,.08))
def relink(o,coll,parent,name,mat):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    coll.objects.link(o);o.parent=parent;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
active_coll=props
def ball(parent,name,pos,size,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(0,0,0));o=relink(bpy.context.object,active_coll,parent,name,mat);o.location=pos;o.scale=size;return o
def box(parent,name,pos,size,mat,bevel=.08):
    bpy.ops.mesh.primitive_cube_add(size=1);o=relink(bpy.context.object,active_coll,parent,name,mat);o.location=pos;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);m=o.modifiers.new('Toy rounded edges','BEVEL');m.width=bevel;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name);o.modifiers.new('Weighted toy normals','WEIGHTED_NORMAL');return o
def torus(parent,name,pos,major,minor,mat,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,major_radius=major,minor_radius=minor)
    o=relink(bpy.context.object,active_coll,parent,name,mat);o.location=pos;o.rotation_euler=rot;return o
assemblies=[]
def assembly(name):
    root=empty(name,props);assemblies.append(root);return root
r=assembly('Toy_Cushion');ball(r,'Cushion velvet',(0,0,.15),(.5,.38,.15),rose);ball(r,'Cushion button',(0,0,.29),(.055,.055,.025),cream)
r=assembly('Toy_Frame');box(r,'Frame rose',(0,0,.37),(.68,.10,.74),rose);box(r,'Frame paper',(0,-.061,.37),(.52,.025,.57),cream,.025);ball(r,'Frame little heart left',(-.055,-.085,.4),(.09,.025,.11),rose);ball(r,'Frame little heart right',(.055,-.085,.4),(.09,.025,.11),rose)
r=assembly('Toy_Oven');box(r,'Oven enamel',(0,0,.44),(.9,.65,.88),cream);box(r,'Oven window',(0,-.34,.37),(.64,.045,.43),rose);box(r,'Oven glass',(0,-.37,.37),(.50,.02,.29),ink,.04);box(r,'Oven handle',(0,-.42,.59),(.44,.07,.055),cream,.025)
for x in [-.24,0,.24]:ball(r,'Oven knob',(x,-.35,.77),(.065,.04,.065),rose)
for x in [-.23,.23]:torus(r,'Oven burner',(x,0,.89),.13,.025,rose)
r=assembly('Toy_Tray');box(r,'Tray porcelain',(0,0,0),(1.18,.64,.065),cream,.03)
for x in [-.59,.59]:torus(r,'Tray handle',(x,0,.02),.105,.025,rose,rot=(math.pi/2,0,0))
r=assembly('Toy_Cup');ball(r,'Cup bowl',(0,0,.14),(.17,.17,.17),rose);ball(r,'Cup tea',(0,0,.265),(.13,.13,.018),tea);torus(r,'Cup handle',(.19,0,.15),.085,.025,rose,rot=(math.pi/2,0,0));ball(r,'Cup saucer',(0,0,.015),(.25,.25,.025),cream)
r=assembly('Toy_Bowl');ball(r,'Bowl porcelain',(0,0,.12),(.38,.32,.2),rose);ball(r,'Bowl dough',(0,0,.27),(.32,.27,.025),cream)
r=assembly('Toy_Spoon');box(r,'Spoon handle',(0,0,-.14),(.055,.055,.4),honey,.02);ball(r,'Spoon scoop',(0,0,-.37),(.11,.065,.10),cream)
r=assembly('Toy_Cutter');torus(r,'Cookie cutter',(0,0,0),.19,.032,rose)
# Heart and star cutters match Nancy's selected cookie, without extra UI.
for shape in ['Heart','Star']:
    r=assembly('Toy_Cutter_'+shape);points=[]
    for i in range(64 if shape=='Heart' else 10):
        a=math.tau*i/(64 if shape=='Heart' else 10)
        if shape=='Heart':x=.20*math.sin(a)**3;y=.20*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/16
        else:radius=.20 if i%2==0 else .095;x=radius*math.sin(a);y=radius*math.cos(a)
        points.append((x,y))
    verts=[];n=len(points)
    for z,radius in [(-.025,1),(-.025,.82),(.025,1),(.025,.82)]:verts.extend((x*radius,y*radius,z) for x,y in points)
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)])
    mesh=bpy.data.meshes.new('Cookie cutter '+shape);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('Cutter '+shape,mesh);props.objects.link(o);o.parent=r;mesh.materials.append(rose)
for i,o in enumerate(assemblies):o.location=(4+(i%4)*1.5,0,(i//4)*1.2)
# Friends are modeled and animated here, not temporary browser stand-ins.
active_coll=friends
momo=empty('Momo',friends);pip=empty('Pip',friends)
for root,name,fur in [(momo,'Momo',honey),(pip,'Pip',white)]:
    ball(root,name+'_Body',(0,0,.35),(.27,.21,.33),fur);ball(root,name+'_Head',(0,0,.78),(.35,.26,.30),fur)
    ball(root,name+'_Tummy',(0,-.20,.34),(.18,.025,.21),cream)
    for side in [-1,1]:
        ball(root,name+'_Eye_'+str(side),(side*.12,-.25,.79),(.025,.014,.036),ink)
        ball(root,name+'_Foot_'+str(side),(side*.15,-.09,.10),(.13,.16,.10),fur)
    ball(root,name+'_Nose',(0,-.27,.70),(.035,.025,.025),rose if name=='Pip' else ink)
    if name=='Momo':
        for side in [-1,1]:
            ball(root,'Momo_Ear',(side*.25,0,1),(.12,.095,.12),fur);ball(root,'Momo_Ear_inner',(side*.25,-.075,1),(.07,.025,.07),cream)
            arm=empty('Momo_Paw_'+('L' if side<0 else 'R'),friends,root);arm.location=(side*.26,0,.5);ball(arm,'Momo_Mitten',(side*.03,-.01,-.12),(.105,.13,.19),fur)
    else:
        for side in [-1,1]:
            ear=empty('Pip_Ear_'+('L' if side<0 else 'R'),friends,root);ear.location=(side*.18,0,.98)
            ball(ear,'Pip_Ear_fur',(0,0,.23),(.10,.09,.31),fur);ball(ear,'Pip_Ear_rose',(0,-.075,.25),(.05,.02,.22),rose)
# Named controls and keys are editable in this same .blend; exporter uses range.
for f in range(1,50,3):
    t=(f-1)/48;p=math.sin(t*math.pi)**2
    arm=bpy.data.objects['Momo_Paw_L'];arm.rotation_euler=(0,1.9*p+.22*math.sin(t*math.pi*6)*p,0);arm.keyframe_insert('rotation_euler',frame=f)
    for sign,side in [(-1,'L'),(1,'R')]:
        ear=bpy.data.objects['Pip_Ear_'+side];ear.rotation_euler=(0,sign*(.16+.22*math.sin(t*math.pi*4)*p),0);ear.keyframe_insert('rotation_euler',frame=f)
    pip.scale=(1,1,1+.07*p);pip.keyframe_insert('scale',frame=f)
momo.location=(4,2,0);pip.location=(6,2,0)
# In Blender, preview the same held props while scrubbing each performance.
# This collection is intentionally excluded from web character exports.
preview=bpy.data.collections.new('GAME — authoring preview (not exported)');s.collection.children.link(preview)
def preview_copy(source,parent,interval):
    o=source.copy();o.name='Preview_'+source.name;preview.objects.link(o);o.parent=parent;o.location=(0,0,0)
    copies=[o]
    for child in source.children_recursive:
        c=child.copy();preview.objects.link(c);c.parent=o;copies.append(c)
    start,end=interval
    for part in copies:
        for f,hidden in [(1,True),(start-1,True),(start,False),(end,False),(end+1,True),(511,True)]:
            part.hide_render=hidden;part.hide_viewport=hidden
            part.keyframe_insert('hide_render',frame=f);part.keyframe_insert('hide_viewport',frame=f)
    return o
for toy,anchor,interval in [('Spoon','Socket_Paw_R',(145,216)),('Cutter','Socket_Paw_R',(217,264)),('Tray','Socket_Tray',(265,312)),('Cup','Socket_Teacup',(451,510))]:
    preview_copy(bpy.data.objects['Toy_'+toy],bpy.data.objects[anchor],interval)
for child in bpy.data.objects['CTRL_Bouquet'].children:
    for f,hidden in [(1,False),(144,False),(145,True),(312,True),(313,False),(450,False),(451,True),(510,True),(511,False)]:
        child.hide_render=hidden;child.hide_viewport=hidden;child.keyframe_insert('hide_render',frame=f);child.keyframe_insert('hide_viewport',frame=f)
s.frame_end=511;s.render.fps=24;s.frame_set(1)
s['friend_clips']=json.dumps({'greet':[1,49]})
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hello_kitty_game.blend'))
print('GAME_ASSETS_AUTHORED:',len(clips),'Kitty clips, hand sockets, 10 prop assemblies, Momo and Pip greetings')
