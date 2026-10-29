"""Build a self-contained Hawaiian plush Hello Kitty fan model. Blender 4.3+.
Run: blender -b --threads 4 --python-exit-code 1 --python create_hawaiian_kitty.py
Outputs go to hawaiian_output/ beside the script; --render adds a portrait render.
Set KITTY_OUTPUT_DIR to select another output directory.
"""
import bpy, math, random, bisect, sys, os
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT=Path(os.environ.get('KITTY_OUTPUT_DIR', str(Path(__file__).resolve().parent/'hawaiian_output')));OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(20261029)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection':bpy.data.collections.remove(c)
collections={}
for name in ['PLUSH — tan fabric','FACE — embroidery','FLOWERS — Hawaiian crown','COSTUME — shells and hula skirt','FIBERS — short plush pile','STUDIO','CONTROLS']:
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);collections[name.split(' —')[0]]=c

def material(name,color,fabric=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=.88 if fabric else .68
    p.inputs['Specular IOR Level'].default_value=.24
    if fabric:
        p.inputs['Sheen Weight'].default_value=.32
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=240;tex.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.37;bump.inputs['Distance'].default_value=.018
        m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
sand=material('Golden honey tan plush',(.53,.28,.105),True)
furm=[material('Tan pile '+str(i),c,True) for i,c in enumerate([(.56,.30,.12),(.68,.40,.19),(.44,.21,.065)])]
brown=material('Dark cocoa embroidered thread',(.065,.021,.008),True)
yellow=material('Sunflower yellow embroidery',(.96,.68,.012),True)
rose=material('Soft pink shell felt',(.88,.24,.43),True)
seam=material('Pink embroidery stitching',(.60,.075,.22),True)
cream=material('Ivory shell embroidery',(.98,.91,.72),True)
greens=[material('Emerald leaf felt '+str(i),c,True) for i,c in enumerate([(.012,.30,.12),(.009,.24,.085),(.024,.36,.145)])]
white=material('Ivory white orchid felt',(.97,.94,.85),True)
red=material('Hibiscus red felt',(.47,.002,.009),True)
lime=material('Fresh lime flower throat',(.54,.70,.018),True)
coral=material('Warm red flower center',(.65,.035,.016),True)
floor=material('Warm porcelain backdrop',(.93,.915,.89))

def organize(o,group):
    for c in list(o.users_collection):c.objects.unlink(o)
    collections[group].objects.link(o)

def finish(o,name,mat,group):
    o.name=name;o.data.materials.append(mat);organize(o,group)
    if o.type=='MESH':
        for f in o.data.polygons:f.use_smooth=True
    return o

def sphere(name,loc,scale,mat=sand,group='PLUSH'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=loc)
    o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,group)

def curve(name,pts,radius,mat,group):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=8;d.bevel_depth=radius;d.bevel_resolution=3
    sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);collections[group].objects.link(o);d.materials.append(mat);return o

def mesh(name,verts,faces,mat,group):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);collections[group].objects.link(o);d.materials.append(mat)
    for p in d.polygons:p.use_smooth=True
    return o

def parent(o,p):
    bpy.context.view_layer.update()
    w=o.matrix_world.copy();o.parent=p;o.matrix_world=w

def control(name,loc,parent_ctrl=None):
    o=bpy.data.objects.new(name,None);collections['CONTROLS'].objects.link(o);o.location=loc;o.empty_display_type='CIRCLE';o.empty_display_size=.35
    if parent_ctrl:parent(o,parent_ctrl)
    return o
root=control('CTRL_Root',(0,0,0));bodyctrl=control('CTRL_Body',(0,0,1.65),root);headctrl=control('CTRL_Head',(0,0,3.45),bodyctrl)
# A broad stuffed head with rounded plush ear caps, fused into one continuous mesh.
head=sphere('Plush head',(0,0,3.40),(1.38,.81,1.08))
parts=[head]
for side in [-1,1]:
    ear=sphere('Rounded plush ear',(side*1.01,0,4.13),(.32,.28,.42))
    ear.rotation_euler[1]=side*.22
    parts.append(ear)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=head;bpy.ops.object.join()
mod=head.modifiers.new('Fused stuffed silhouette','REMESH');mod.mode='VOXEL';mod.voxel_size=.028;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=head.modifiers.new('Soft stuffed edges','SMOOTH');mod.factor=1.1;mod.iterations=5;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=head.modifiers.new('Smooth fabric surface','SUBSURF');mod.levels=1;bpy.ops.object.modifier_apply(modifier=mod.name)
parent(head,headctrl)
body=sphere('Stuffed tan body',(0,.02,1.55),(.76,.51,.92));parent(body,bodyctrl)
plush=[(head,21000),(body,6500)]
for side in [-1,1]:
    foot=sphere('Plush foot '+str(side),(side*.43,-.10,.40),(.43,.56,.39));parent(foot,root);plush.append((foot,3500))
left=sphere('Raised rounded paw',(-.94,-.48,2.33),(.34,.34,.54));left.rotation_euler[1]=-.43
right=sphere('Outstretched rounded paw',(.97,-.22,1.98),(.47,.33,.30));right.rotation_euler[1]=-.17
for o,side in [(left,'L'),(right,'R')]:
    armctrl=control('CTRL_Paw_'+side,tuple(o.location),bodyctrl);parent(o,armctrl);plush.append((o,3500))
# Short individually modeled fibers; no external maps or hair add-ons.
def fibers(o,count):
    bpy.context.view_layer.update()
    d=o.data;d.calc_loop_triangles();tris=list(d.loop_triangles);weights=[];total=0
    for t in tris:total+=t.area;weights.append(total)
    curves=[]
    for i,m in enumerate(furm):
        c=bpy.data.curves.new(o.name+' pile '+str(i),'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=.0014;c.bevel_resolution=0;c.materials.append(m)
        ob=bpy.data.objects.new(c.name,c);collections['FIBERS'].objects.link(ob);ob.parent=o;curves.append(c)
    for _ in range(count):
        t=tris[bisect.bisect_left(weights,rng.random()*total)]
        a,b,c=[d.vertices[j] for j in t.vertices];u=sqrt(rng.random());v=rng.random();w=(1-u,u*(1-v),u*v)
        p=a.co*w[0]+b.co*w[1]+c.co*w[2];n=(a.normal*w[0]+b.normal*w[1]+c.normal*w[2]).normalized()
        tangent=Vector((rng.uniform(-.5,.5),rng.uniform(-.5,.5),-.8));tangent-=n*tangent.dot(n);tangent.normalize()
        length=rng.uniform(.007,.014)
        sp=curves[rng.choices([0,1,2],[.55,.30,.15])[0]].splines.new('POLY');sp.points.add(2)
        for q,(h,lean) in zip(sp.points,[(.001,0),(length*.62,length*.22),(length,length*.65)]):
            pt=p+n*h+tangent*lean;q.co=(*pt,1);q.radius=1 if h<length else .25
for o,n in plush:fibers(o,n)
# Flat cocoa embroidery sits against the curved fabric face.
for side in [-1,1]:
    eye=sphere('Embroidered eye '+str(side),(side*.57,-.756,3.43),(.102,.030,.157),brown,'FACE');parent(eye,headctrl)
    for j,dz in enumerate([.22,0,-.22]):
        pts=[]
        for x,z in [(side*.97,3.33+dz),(side*1.16,3.33+dz+.015),(side*1.34,3.33+dz+.04)]:
            y=-.81*sqrt(max(.03,1-(x/1.38)**2-((z-3.4)/1.08)**2))-.024
            pts.append((x,y,z))
        wh=curve('Cocoa whisker '+str(side)+' '+str(j),pts,.016,brown,'FACE');parent(wh,headctrl)
nose=sphere('Yellow embroidered oval nose',(0,-.816,3.18),(.13,.038,.086),yellow,'FACE');parent(nose,headctrl)
# Thread traces make the eyes and nose read as embroidery instead of plastic.
for side in [-1,1]:
    for j in range(13):
        z=3.43-.14+j*.28/12;r=.095*sqrt(max(0,1-((z-3.43)/.157)**2))
        ob=curve('Eye stitch',[(side*.57-r,-.785,z),(side*.57,-.790,z+.005),(side*.57+r,-.785,z)],.0023,brown,'FACE');parent(ob,headctrl)
for j in range(12):
    x=-.115+j*.23/11;h=.078*sqrt(max(0,1-(x/.13)**2))
    ob=curve('Nose stitch',[(x,-.854,3.18-h),(x,-.858,3.18+h)],.0026,yellow,'FACE');parent(ob,headctrl)
# Felt flowers: broad, cupped petals around small embroidered throats.
def flower(name,center,R,mat,petals=5,turn=0,hibiscus=False):
    center=Vector(center)
    if name=='Red hibiscus':
        for k in range(5):
            a=turn+2*pi*k/5;axis=Vector((sin(a),0,cos(a)))
            ob=sphere(name+' plush petal '+str(k),tuple(center+axis*R*.46),(R*.49,.075,R*.62),mat,'FLOWERS');ob.rotation_euler[1]=a;parent(ob,headctrl)
        return
    for k in range(petals):
        a=turn+2*pi*k/petals;axis=Vector((sin(a),0,cos(a)));across=Vector((cos(a),0,-sin(a)))
        if name.endswith('orchid'):
            ob=sphere(name+' soft petal '+str(k),tuple(center+axis*R*.45),(R*.43,.030,R*.58),mat,'FLOWERS');ob.rotation_euler[1]=a;parent(ob,headctrl)
            continue
        verts=[];faces=[];rows=14;cols=9
        for i in range(rows):
            t=i/(rows-1);r=R*(.07+.93*t);width=R*(.36 if hibiscus else .48)*(sin(pi*t)**.65+.015)
            for j in range(cols):
                u=2*j/(cols-1)-1;p=center+axis*r+across*width*u
                p.y-=.05*sin(pi*t)+.06*t*t-.045*u*u*sin(pi*t)
                verts.append(tuple(p))
        for i in range(rows-1):
            for j in range(cols-1):q=i*cols+j;faces.append((q,q+1,q+cols+1,q+cols))
        ob=mesh(name+' petal '+str(k),verts,faces,mat,'FLOWERS');sol=ob.modifiers.new('Soft felt thickness','SOLIDIFY');sol.thickness=.018;parent(ob,headctrl)
    if not hibiscus:
        ob=sphere(name+' lime throat',tuple(center+Vector((0,-.055,0))),(.075,.04,.10),lime,'FLOWERS');parent(ob,headctrl)
        ob=curve(name+' center thread',[tuple(center+Vector((-.025,-.105,-.025))),tuple(center+Vector((.015,-.11,.02))),tuple(center+Vector((.027,-.105,-.015)))],.012,coral,'FLOWERS');parent(ob,headctrl)
for name,pos,r,turn in [('Left orchid',(-.87,-.57,4.08),.40,.4),('Top orchid',(-.20,-.59,4.30),.36,-.1),('Right orchid',(.43,-.58,4.24),.35,.4)]:flower(name,pos,r,white,turn=turn)
flower('Red hibiscus',(1.00,-.54,4.13),.55,red,turn=.15,hibiscus=True)
flower('Ivory hibiscus heart',(1.00,-.64,4.13),.25,white,petals=6,turn=.2,hibiscus=True)
stamen=curve('Golden hibiscus stamen',[(1.00,-.72,4.13),(1.14,-.77,4.30),(1.20,-.75,4.52)],.026,yellow,'FLOWERS');parent(stamen,headctrl)
for x,z in [(1.16,4.52),(1.23,4.55),(1.25,4.49)]:
    ob=sphere('Hibiscus pollen tip',(x,-.75,z),(.045,.032,.04),yellow,'FLOWERS');parent(ob,headctrl)
# Emerald felt skirt, each hanging panel individually editable.
for i in range(17):
    a=2*pi*i/17;bottom=.58+rng.uniform(-.045,.07);verts=[];faces=[];rows=9;cols=5
    for j in range(rows):
        t=j/(rows-1);r=.69+.13*t
        for k in range(cols):
            u=2*k/(cols-1)-1;aa=a+u*.160*(1-.10*t)
            z=1.34+(bottom-1.34)*t+.025*sin(t*pi)*u*u
            if j==rows-1:z+=.045*(1-u*u)
            verts.append((r*cos(aa),r*.82*sin(aa),z))
    for j in range(rows-1):
        for k in range(cols-1):q=j*cols+k;faces.append((q,q+1,q+cols+1,q+cols))
    ob=mesh('Hula felt panel %02d'%i,verts,faces,greens[i%3],'COSTUME');sol=ob.modifiers.new('Thick leaf felt','SOLIDIFY');sol.thickness=.026;be=ob.modifiers.new('Soft felt edge','BEVEL');be.width=.009;be.segments=2;parent(ob,bodyctrl)
bpy.ops.mesh.primitive_torus_add(major_radius=.69,minor_radius=.063,major_segments=96,minor_segments=16,location=(0,0,1.34))
waist=finish(bpy.context.object,'Pink felt waistband',rose,'COSTUME');waist.scale.y=.82;parent(waist,bodyctrl)
# Pink scallop shells with stitched borders and ivory fan ribs.
for side in [-1,1]:
    cx=side*.34;base=Vector((cx,-.56,1.48));outline=[base]
    for i in range(51):
        a=-1.15+2.3*i/50;r=.43*(1+.055*cos(a*12));outline.append(base+Vector((sin(a)*r,-.075,cos(a)*r)))
    ob=mesh('Pink shell '+str(side),[tuple(p) for p in outline],[(0,j,j+1) for j in range(1,len(outline)-1)],rose,'COSTUME')
    sol=ob.modifiers.new('Stuffed felt shell','SOLIDIFY');sol.thickness=.065;be=ob.modifiers.new('Plush rounded shell edges','BEVEL');be.width=.025;be.segments=3;parent(ob,bodyctrl)
    for a in [-.80,-.40,0,.40,.80]:
        pts=[tuple(base+Vector((sin(a)*r,-.119,cos(a)*r))) for r in [.18,.26,.34]]
        ob=curve('Ivory shell rib',pts,.010,cream,'COSTUME');parent(ob,bodyctrl)
    for j in range(0,49,2):
        a=-1.15+2.3*(j+.2)/50;b=-1.15+2.3*(j+1.0)/50
        pts=[tuple(base+Vector((sin(v)*.398,-.118,cos(v)*.398))) for v in [a,b]]
        ob=curve('Shell border stitch',pts,.004,seam,'COSTUME');parent(ob,bodyctrl)
ob=curve('Pink shell top connecting cord',[(-.25,-.62,1.60),(0,-.64,1.59),(.25,-.62,1.60)],.024,rose,'COSTUME');parent(ob,bodyctrl)
# Enlarge the complete head assembly, including its face and crown, around the
# existing posing pivot. The lower jaw overlaps more of the torso, matching the
# reference's large plush head and short visible body.
bodyctrl.scale=(1.28,1,1)
headctrl.scale=(1.22/1.28,1.08,1.24)
# Broaden the stuffed torso and outfit without spreading the paws away from the
# cheeks. Slightly wider feet restore the reference's squat, padded silhouette.
for name in ['CTRL_Paw_L','CTRL_Paw_R']:
    ctrl=bpy.data.objects[name]
    ctrl.location.x/=1.28
    ctrl.scale.x=1/1.28
for side in [-1,1]:
    foot=bpy.data.objects['Plush foot '+str(side)]
    foot.location.x*=1.15
    foot.scale.x*=1.15
bpy.context.view_layer.update()
# Clean warm-white studio for a reference-style product portrait.
floor.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.93,.915,.89,1)
floor.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=3
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.005));finish(bpy.context.object,'Seamless ivory studio',floor,'STUDIO')
def aim(o,point):o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Large soft key',(-4,-6,8),850,5),('Soft frontal fill',(4,-5,5),600,4),('Top fabric rim',(1,3,7),950,4)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);collections['STUDIO'].objects.link(o);o.location=loc;aim(o,(0,0,2.3))
bpy.ops.object.camera_add(location=(.25,-13.5,5.4));camera=bpy.context.object;camera.name='Plush portrait camera';organize(camera,'STUDIO');aim(camera,(0,-.04,2.52));camera.data.type='ORTHO';camera.data.ortho_scale=6.0
s=bpy.context.scene;s.camera=camera;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32;s.eevee.use_raytracing=False
s.world.color=(.28,.28,.28);s.render.resolution_x=1080;s.render.resolution_y=1350;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.05
s.render.image_settings.file_format='PNG';s.render.filepath='//hawaiian_kitty_preview.png';s.render.film_transparent=False
s['About']='Hawaiian plush fan model inspired by the supplied toy reference: honey tan pile, cocoa embroidery, white orchids and red hibiscus, pink shell top and emerald felt skirt.'
s['Controls']='CTRL_Root, CTRL_Body, CTRL_Head and CTRL_Paw_L/R are editable posing controls. No animation is baked. Hide FIBERS collection for faster viewport editing.'
text=bpy.data.texts.new('START HERE');text.write('HAWAIIAN PLUSH HELLO KITTY\nBlender 4.3+. Self-contained materials and modeled short fibers; no external textures or add-ons.\nF12: render the portrait. Image > Save As exports a PNG for Higgsfield.\nCamera and output are portrait 1080 x 1350.\nCTRL_* empties pose the head, body and paws. Hide FIBERS for a faster viewport.\nThe flower crown, embroidered face, shell top, skirt and fibers have separate named collections.\nThis is an editable decorative model, not a production skeletal rig or watertight print mesh.\n')
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_extras=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hello_kitty_hawaiian_plush.blend'))
assert head.parent==headctrl and s.camera and len(collections['FLOWERS'].objects)>20
print('HAWAIIAN_PLUSH_BUILD_COMPLETE',flush=True)
if '--render' in sys.argv:
    if '--draft' in sys.argv:s.render.resolution_percentage=70;s.eevee.taa_render_samples=16
    s.render.filepath=str(OUT/('draft.png' if '--draft' in sys.argv else 'hawaiian_kitty_preview.png'))
    bpy.ops.render.render(write_still=True)
