"""Build Nancy's editable studio home and a compact, matching web export.
Run: blender -b --python-exit-code 1 --python create_studio_home.py
Coordinates in helpers are browser x / height / depth; Blender uses Z-up.
The .blend keeps separate editable furniture pieces. The GLB joins each station
for a smaller browser draw budget and preserves the named interaction roots.
"""
import bpy, math, json, hashlib, shutil, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):bpy.data.materials.remove(data)
scene=bpy.context.scene
collection=bpy.data.collections.new('NANCY — studio home');scene.collection.children.link(collection)
materials={};stations=[];anchors={};current=None

def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,color,rough=.8,metal=0,glow=0):
    color=color.lstrip('#');rgb=[linear(int(color[i:i+2],16)/255) for i in [0,2,4]]
    m=bpy.data.materials.new('Studio '+name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if glow:p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=glow
    materials[name]=m;return m
cream=mat('cream','#fff1dd');wall=mat('wall','#e8bacb');wood=mat('oak','#d4ac82');edge=mat('oak edge','#b98e68');pink=mat('rose','#d78da8');blush=mat('blush','#f0c6d0');white=mat('linen','#fff8ed');sage=mat('sage','#a6bfa7');mint=mat('mint','#cee0d6');ink=mat('ink','#4d3d42');glass=mat('window','#b6d6dc',.4);metal=mat('metal','#b9c8c5',.45,.28);honey=mat('honey','#d7ae6c');leaves=mat('leaves','#789676');lavender=mat('lavender','#c0b1ce');tile=mat('tile','#dce8e3');water=mat('water','#c4e2e3',.35);light=mat('warm light','#ffe1a0',.6,0,.7)

def cv(p):return (p[0],-p[2],p[1])
def station(name,pos=(0,0,0),yaw=0,role=None,parent=None):
    o=bpy.data.objects.new(name,None);collection.objects.link(o);o.location=cv(pos);o.rotation_euler.z=yaw
    if parent:o.parent=parent
    else:stations.append(o)
    o.empty_display_type='PLAIN_AXES';o.empty_display_size=.22
    o['studio_station']=name
    if role:o['studio_action']=role
    return o

def attach(o,name,pos,material,parent=None):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);o.parent=parent or current;o.location=cv(pos);o.data.materials.append(material)
    return o

def box(name,pos,size,material,bevel=.045,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1);o=attach(bpy.context.object,name,pos,material,parent);o.scale=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Soft furniture edges','BEVEL');m.width=min(bevel,min(size)*.43);m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name)
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def ball(name,pos,size,material,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10);o=attach(bpy.context.object,name,pos,material,parent);o.scale=(size[0],size[2],size[1]);
    for p in o.data.polygons:p.use_smooth=True
    return o

def cylinder(name,pos,radius,height,material,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=height);o=attach(bpy.context.object,name,pos,material,parent)
    bevel=o.modifiers.new('Soft rim','BEVEL');bevel.width=min(.025,height*.2);bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name);o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def tube(name,points,radius,material,parent=None):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=2;data.resolution_u=8
    sp=data.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for v,p in zip(sp.bezier_points,points):v.co=cv(p);v.handle_left_type=v.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,data);collection.objects.link(o);o.parent=parent or current;data.materials.append(material);return o

def anchor(name,pos,parent=None,yaw=0):
    o=station('Anchor_'+name,pos,yaw,parent=parent or current);o['studio_anchor']=name
    return o

def flower(name,pos,scale=.4,parent=None):
    holder=station(name,pos,parent=parent or current)
    cylinder(name+' pot',(0,.14,0),.19,.28,cream,holder)
    for i in range(3):
        x=(i-1)*.12;z=(i%2)*.1
        tube(name+' stem',[(0,.25,0),(x,.47,z),(x,.69+i*.04,z)],.015,leaves,holder)
        ball(name+' leaf',(x*.5,.44,z),(.12,.04,.065),sage,holder)
        for k in range(5):
            a=math.tau*k/5
            ball(name+' petal',(x+math.cos(a)*.08,.71+i*.04+math.sin(a)*.08,z),(.066,.066,.034),pink if i%2 else white,holder)
        ball(name+' centre',(x,.71+i*.04,z+.03),(.035,.035,.025),honey,holder)
    holder.scale=(scale,scale,scale);return holder

def cup(name,pos,color=pink,parent=None,scale=1):
    p=station(name,pos,parent=parent or current);cylinder(name+' saucer',(0,.018,0),.19,.035,cream,p)
    cylinder(name+' body',(0,.14,0),.12,.24,color,p);cylinder(name+' tea',(0,.265,0),.096,.012,honey,p)
    tube(name+' handle',[(.1,.22,0),(.21,.22,0),(.22,.1,0),(.1,.08,0)],.025,color,p);p.scale=(scale,scale,scale);return p

def frame(name,pos,parent=None,scale=1):
    p=station(name,pos,parent=parent or current);box(name+' border',(0,.32,0),(.52,.64,.065),edge,.04,p);box(name+' paper',(0,.32,.04),(.43,.54,.018),white,.01,p)
    ball(name+' heart L',(-.055,.35,.058),(.09,.1,.025),pink,p);ball(name+' heart R',(.055,.35,.058),(.09,.1,.025),pink,p)
    p.scale=(scale,scale,scale);return p

# Warm cutaway shell: room 11.6 x 10 with space around every activity.
current=station('Studio_Shell')
box('Soft green foundation',(0,-.35,0),(12,.45,10.4),mint,.23)
box('Oak floor slab',(0,-.05,0),(11.7,.28,10.1),edge,.12)
box('Floor finish',(0,.105,0),(11.5,.05,9.95),wood,.03)
for i in range(22):
    x=-5.45+i*.51
    box('Floorboard seam',(x,.133,0),(.013,.005,9.9),edge,.002)
    for j in range(6):box('Board end',(x+.25,.134,-4.5+j*1.65+(i%2)*.5),(.49,.005,.012),edge,.002)
current=station('Studio_BackWall')
box('Pink back wall',(0,2.1,-5.04),(11.85,4.0,.16),wall,.035)
box('Cream back skirting',(0,.3,-4.94),(11.65,.28,.1),cream,.025)
box('Back cornice',(0,4.08,-4.94),(11.8,.13,.16),cream,.025)
for i in range(26):box('Back wallpaper stripe',(-5.65+i*.445,2.18,-4.947),(.07,3.6,.012),blush,.001)
current=station('Studio_LeftWall')
box('Pink left wall',(-5.86,2.1,0),(.16,4,10.15),wall,.035)
box('Left skirting',(-5.76,.3,0),(.1,.28,9.95),cream,.025)
box('Left cornice',(-5.76,4.08,0),(.16,.13,10.1),cream,.025)
for i in range(23):box('Left wallpaper stripe',(-5.767,2.18,-4.8+i*.43),(.012,3.6,.07),blush,.001)
# Source anchors also drive the browser placements: export is the single layout.
window=station('Studio_Window',(-5.74,2.55,-2),math.pi/2)
current=window
box('Blue window',(0,0,0),(2.1,2.15,.07),glass,.025)
for x in [-1.08,0,1.08]:box('Window vertical bar',(x,0,.055),(.07,2.3,.09),cream,.012)
for y in [-1.12,0,1.12]:box('Window horizontal bar',(0,y,.06),(2.24,.07,.1),cream,.012)
box('Wide windowsill',(0,-1.2,.18),(2.5,.12,.52),cream,.025)
for side in [-1,1]:
    for k in range(4):cylinder('Curtain fold',(side*(1.12+k*.075),.02,.13),.085,2.5,blush)
tube('Curtain rail',[(-1.5,1.3,.1),(0,1.3,.1),(1.5,1.3,.1)],.035,edge)
anchor('window',(0,-1.12,.3))
# Bed and bedside lamp: curved upholstered headboard, mattress, duvet and pillows.
current=station('Studio_Bed',(-3.95,.13,-2.4),role='sleep')
for x in [-.9,.9]:
    for z in [-1.2,1.2]:cylinder('Bed wooden foot',(x,.18,z),.075,.35,edge)
box('Bed frame',(0,.3,0),(2.4,.38,3.25),cream,.12)
box('Padded headboard',(0,1.05,-1.6),(2.55,1.45,.22),blush,.18)
box('Mattress',(0,.59,0),(2.28,.32,3.12),white,.14)
box('Rose duvet',(0,.82,.36),(2.32,.24,2.42),pink,.15)
box('Duvet folded edge',(0,.94,-.75),(2.3,.12,.3),blush,.07)
for x in [-.55,.55]:
    pillow=ball('Soft bed pillow',(x,.9,-1.14),(.5,.17,.35),white);pillow.rotation_euler.z=x*.08
for x in [-.83,-.28,.28,.83]:
    for z in [-.35,.28,.91]:ball('Duvet stitched dot',(x,.947,z),(.024,.008,.024),blush)
anchor('bed',(0,1,.25))
current=station('Studio_Bedside',(-2.35,.13,-3.5))
box('Nightstand base',(0,.42,0),(.65,.74,.65),cream,.07);box('Nightstand top',(0,.82,0),(.73,.1,.73),wood,.035)
box('Drawer front',(0,.54,.34),(.53,.25,.035),blush,.025);ball('Drawer knob',(0,.54,.385),(.045,.035,.035),edge)
cylinder('Bedside lamp foot',(0,.9,0),.14,.05,edge);cylinder('Bedside lamp stem',(0,1.1,0),.024,.35,edge)
ball('Bedside lamp shade',(0,1.31,0),(.24,.19,.24),light)
anchor('lamp_bed',(0,1.31,0))
# Wardrobe stands beside the sleeping area; it opens the existing clothing UI.
current=station('Studio_Wardrobe',(5.02,.13,2.55),role='wardrobe')
box('Wardrobe body',(0,1.3,0),(1.15,2.6,.78),cream,.09)
for x in [-.28,.28]:
    box('Wardrobe rose door',(x,1.35,.42),(.53,2.35,.055),blush,.045);ball('Wardrobe brass pull',(x*.37,1.35,.47),(.034,.07,.034),honey)
box('Wardrobe crown',(0,2.65,0),(1.28,.13,.87),wood,.04)
anchor('wardrobe',(0,1.6,.5))
# Compact tiled bathroom with a wash basin, shower and toilet. Half-height
# partitions make its layout readable in the roofless browser view.
current=station('Studio_Bathroom',(-.3,.13,-3.67))
box('Bathroom tile base',(0,.015,0),(2.25,.035,2.5),tile,.025)
for i in range(5):
    for j in range(5):
        if (i+j)%2==0:box('Bathroom mint tile',(-.9+i*.45,.038,-1+j*.5),(.43,.012,.48),white,.006)
box('Bathroom left partition',(-1.17,.84,0),(.12,1.68,2.6),mint,.05)
box('Bathroom front screen',(-.44,.75,1.28),(1.55,1.5,.12),mint,.05)
box('Screen top rail',(-.44,1.52,1.28),(1.65,.09,.18),wood,.025)
# Shower tray is actually recessed, with separate rim and shallow basin.
box('Shower tray bottom',(-.56,.13,-.59),(.94,.12,1.12),cream,.08)
for x in [-1.03,-.09]:box('Shower tray side',(x,.23,-.59),(.055,.18,1.15),white,.025)
for z in [-1.15,-.03]:box('Shower tray end',(-.56,.23,z),(.94,.18,.055),white,.025)
cylinder('Shower drain',(-.56,.2,-.55),.055,.012,metal)
tube('Shower pipe',[(-.95,.37,-1.13),(-.95,2.32,-1.13),(-.65,2.43,-.98),(-.46,2.39,-.91)],.025,metal)
ball('Shower head',(-.45,2.36,-.89),(.17,.035,.12),metal)
tube('Curtain rod',[(-1.08,2.38,.01),(-.56,2.38,.01),(.02,2.38,.01)],.025,metal)
for x in [-1.02,-.92,-.82]:cylinder('Gathered shower curtain',(x,1.4,.04),.085,1.78,sage)
# Toilet: tank, lid and a hollow-looking oval bowl, supported on a pedestal.
box('Toilet tank',(.65,.73,-.91),(.56,.85,.32),white,.12)
box('Toilet tank lid',(.65,1.18,-.91),(.61,.09,.37),cream,.035)
ball('Toilet pedestal',(.65,.3,-.56),(.18,.3,.23),white)
ball('Toilet bowl',(.65,.57,-.45),(.34,.2,.43),white)
ball('Toilet seat opening',(.65,.744,-.42),(.23,.018,.31),ink)
ball('Toilet seat water',(.65,.752,-.42),(.18,.012,.24),water)
ball('Toilet flush',(.82,1.18,-.91),(.035,.012,.035),metal)
# Wash cabinet and basin on the front wall of the alcove.
box('Wash cabinet',(-.6,.47,.65),(.72,.85,.55),cream,.065)
box('Wash cabinet front',(-.6,.5,.944),(.6,.62,.035),sage,.03)
box('Wash basin bottom',(-.6,.94,.65),(.66,.06,.48),white,.04)
for x in [-.94,-.26]:box('Wash basin side',(x,1,.65),(.045,.12,.5),white,.02)
for z in [.41,.89]:box('Wash basin lip',(-.6,1,z),(.66,.12,.045),white,.02)
tube('Wash tap',[(-.6,1.03,.49),(-.6,1.3,.49),(-.6,1.3,.66),(-.6,1.21,.69)],.025,metal)
box('Bath mirror frame',(-1.09,1.94,.6),(.08,.72,.65),wood,.035)
box('Bath mirror',(-1.04,1.94,.6),(.02,.62,.55),glass,.015)
box('Folded bathroom towel',(.55,.09,.63),(.61,.1,.54),blush,.035)
# Kitchen counter with real sink opening, stovetop, oven and a two-door fridge.
current=station('Studio_Kitchen',(0,.13,0),role='baking')
for x in [1.75,2.6]:
    box('Kitchen lower cabinet',(x,.39,-4.15),(.82,.76,1.0),cream,.045)
    box('Kitchen cabinet door',(x,.5,-3.627),(.74,.74,.045),sage,.035)
    box('Kitchen pull',(x,.79,-3.58),(.24,.035,.04),edge,.012)
# Separate counter segments leave an opening for the sink.
for x,w in [(1.42,.22),(2.76,.45),(3.57,1.14)]:box('Kitchen worktop',(x,1.02,-4.15),(w,.12,1.1),wood,.035)
for z in [-4.66,-3.64]:box('Sink counter strip',(2.04,1.02,z),(.99,.12,.09),wood,.02)
box('Sink basin bottom',(2.04,.85,-4.15),(.84,.06,.84),metal,.06)
for x in [1.62,2.46]:box('Sink side',(x,.94,-4.15),(.04,.17,.87),metal,.015)
for z in [-4.57,-3.73]:box('Sink rim',(2.04,.94,z),(.84,.17,.04),metal,.015)
cylinder('Sink drain',(2.04,.891,-4.15),.045,.008,ink)
tube('Kitchen tap',[(2.04,1.03,-4.5),(2.04,1.5,-4.5),(2.04,1.55,-4.25),(2.04,1.35,-4.08)],.035,metal)
# Oven cavity door and controls are deliberately separate editable pieces.
box('Oven body',(3.57,.48,-4.15),(1.05,.94,1.02),cream,.065)
box('Oven dark inset',(3.57,.43,-3.61),(.83,.57,.04),ink,.035)
box('Oven rose door',(3.57,.43,-3.58),(.78,.51,.045),pink,.045)
box('Oven glass',(3.57,.43,-3.549),(.61,.34,.018),ink,.035)
box('Oven handle',(3.57,.73,-3.5),(.61,.055,.075),cream,.02)
for x in [3.25,3.57,3.89]:ball('Oven knob',(x,.87,-3.57),(.06,.06,.035),pink)
for x in [3.3,3.85]:
    cylinder('Stove burner',(x,1.095,-4.15),.18,.03,ink)
    cylinder('Stove inner ring',(x,1.115,-4.15),.115,.025,metal)
# Blender-authored kettle with spout and handle.
ball('Kettle body',(3.3,1.36,-4.15),(.22,.24,.22),blush)
ball('Kettle lid',(3.3,1.6,-4.15),(.15,.035,.15),cream)
tube('Kettle handle',[(3.1,1.43,-4.15),(3.1,1.73,-4.15),(3.5,1.73,-4.15),(3.5,1.43,-4.15)],.035,edge)
tube('Kettle spout',[(3.47,1.38,-4.15),(3.65,1.46,-4.15),(3.68,1.55,-4.15)],.055,blush)
fridge=station('Studio_Fridge',(5.02,0,-4.13),parent=current)
box('Fridge cabinet',(0,1.24,0),(1.05,2.48,1.12),cream,.12,parent=fridge)
for y,h in [(1.84,1.0),(.65,1.26)]:
    box('Fridge door',(0,y,.59),(.94,h,.075),mint,.06,parent=fridge)
    box('Fridge handle',(-.34,y,.65),(.045,.37,.06),metal,.02,parent=fridge)
box('Fridge little note',(.16,1.91,.64),(.26,.29,.015),white,.01,parent=fridge)
ball('Fridge heart magnet',(.16,2.05,.665),(.05,.04,.025),pink,parent=fridge)
anchor('oven',(3.57,.56,-3.53));anchor('kitchen',(2.7,1.6,-3.5))
# Upper cupboards are their own cutaway group.
current=station('Studio_UpperCabinets')
for x in [1.75,2.65,3.55]:
    box('Upper cupboard',(x,2.6,-4.68),(.84,.95,.55),cream,.045)
    box('Cupboard inset',(x,2.6,-4.38),(.74,.81,.04),blush,.03)
    ball('Cupboard knob',(x+.23,2.54,-4.34),(.035,.035,.025),edge)
box('Kitchen tile backsplash',(2.65,1.65,-4.91),(2.75,.9,.055),tile,.015)
for x in [1.45,1.9,2.35,2.8,3.25,3.7]:box('Backsplash vertical grout',(x,1.65,-4.87),(.012,.86,.012),white,.002)
box('Backsplash grout',(2.65,1.65,-4.87),(2.7,.012,.012),white,.002)
# A two-person dining table with real chairs, place settings and biscuits.
current=station('Studio_Dining',(3.6,.13,-.8))
cylinder('Dining table pedestal',(0,.48,0),.09,.94,edge);cylinder('Dining foot',(0,.08,0),.5,.1,wood)
cylinder('Dining round top',(0,1.02,0),.82,.12,cream)
for side in [-1,1]:
    chair=station('Dining chair '+str(side),(side*1.2,0,0),-side*math.pi/2,parent=current)
    box('Dining chair seat',(0,.57,0),(.65,.15,.64),blush,.08,parent=chair)
    box('Dining chair back',(0,1,-.28),(.7,.92,.12),cream,.09,parent=chair)
    for x in [-.23,.23]:
        for z in [-.22,.22]:cylinder('Dining chair foot',(x,.26,z),.04,.53,edge,parent=chair)
cup('Dining rose cup',(-.35,1.1,.05),pink,scale=.8);cup('Dining sage cup',(.35,1.1,-.1),sage,scale=.8)
cylinder('Cookie plate',(0,1.1,.3),.22,.025,white)
for x in [-.1,.08]:
    cylinder('Tiny biscuit',(x,1.14,.3),.082,.055,honey)
    for t in [-.03,.03]:ball('Biscuit chocolate',(x+t,1.171,.32),(.009,.005,.009),ink)
# Lounge: a rounded loveseat against the window wall, low table, book and lamp.
current=station('Studio_Sofa',(-4.85,.13,.6),math.pi/2,role='relax')
for x in [-1,1]:
    for z in [-.28,.28]:cylinder('Sofa foot',(x,.12,z),.06,.23,edge)
box('Sofa base',(0,.37,0),(2.6,.49,1.03),sage,.17)
box('Sofa back',(0,.93,-.41),(2.7,1.24,.24),mint,.18)
for x in [-1.21,1.21]:box('Sofa soft arm',(x,.7,0),(.26,.72,1.1),mint,.11)
for x in [-.58,.58]:
    box('Sofa seat cushion',(x,.68,.05),(1.08,.2,.83),sage,.09)
    ball('Sofa pillow',(x,.99,-.19),(.34,.32,.14),blush)
anchor('reading',(0,.89,.7));anchor('nook',(.52,.8,.13));anchor('chair',(-.55,.8,.15))
current=station('Studio_CoffeeTable',(-2.9,.13,1.1))
box('Coffee table top',(0,.57,0),(1.4,.12,.86),cream,.14)
for x in [-.48,.48]:
    for z in [-.23,.23]:cylinder('Coffee table leg',(x,.28,z),.045,.53,edge)
book=station('Open little book',(-.18,.65,.03),.12,parent=current)
box('Book cover',(0,.015,0),(.58,.045,.39),pink,.015,parent=book)
for x in [-.14,.14]:box('Open book pages',(x,.055,0),(.26,.06,.35),white,.014,parent=book)
for i in range(3):box('Book line',(-.14,.088,-.1+i*.08),(.18,.006,.007),edge,.001,parent=book)
flower('Coffee flowers',(.45,.63,-.03),.44)
# Six cubbies fit the same earned plush collection; anchors replace old hardcoded positions.
current=station('Studio_Shelf',(-5.05,.13,3.5),math.pi/2)
box('Collection back',(0,1.22,-.24),(2.84,2.38,.07),blush,.035)
for x in [-1.45,1.45]:box('Collection side',(x,1.22,0),(.12,2.45,.72),cream,.025)
for y in [.31,1.26,2.22]:box('Collection shelf',(0,y,0),(2.98,.11,.78),cream,.025)
for x in [-.48,.48]:box('Collection divider',(x,1.27,0),(.065,1.86,.7),cream,.015)
for x in [-1.2,1.2]:cylinder('Collection foot',(x,.13,0),.055,.26,edge)
for row,y in enumerate([.38,1.33]):
    for col,x in enumerate([-.96,0,.96]):anchor('shelf_'+str(row*3+col),(x,y,.22))
# Desk with personal envelope, lamp and photograph. It opens Nancy's real letter.
current=station('Studio_Desk',(2.6,.13,2.7),role='letter')
box('Writing desktop',(0,1.02,0),(2.05,.13,.88),wood,.07)
for x in [-.83,.83]:
    for z in [-.29,.29]:cylinder('Desk foot',(x,.5,z),.055,1,edge)
box('Desk drawer',(.62,.78,0),(.57,.3,.68),cream,.045)
ball('Desk drawer pull',(.62,.78,.37),(.045,.035,.035),pink)
box('Envelope paper',(-.22,1.107,.08),(.67,.035,.4),white,.015)
ball('Envelope seal',(-.22,1.133,.08),(.065,.012,.06),pink)
frame('Desk photograph',(.67,1.1,-.2),scale=.65)
cylinder('Desk lamp base',(-.73,1.12,-.12),.14,.045,edge)
tube('Desk lamp neck',[(-.73,1.14,-.12),(-.73,1.7,-.12),(-.53,1.82,-.1)],.026,edge)
ball('Desk lamp shade',(-.51,1.78,-.1),(.2,.14,.18),light)
anchor('lamp_desk',(-.51,1.78,-.1))
box('Desk stool seat',(0,.57,.95),(.7,.17,.65),blush,.1)
for x in [-.24,.24]:
    for z in [.72,1.18]:cylinder('Desk stool foot',(x,.26,z),.035,.52,edge)
anchor('desk',(0,1.2,.25));anchor('table',(.55,1.1,.18))
# Main soft rug and a few deliberate plants keep the centre open.
current=station('Studio_Rug')
carpet=cylinder('Rose oval rug',(0,.155,.65),2.1,.045,pink);carpet.scale.y=.72
inset=cylinder('Rug inner oval',(0,.18,.65),1.98,.015,blush);inset.scale.y=.72
anchor('rug',(1.4,.2,.9));anchor('floor_nook',(-1.5,.145,2.1))
anchor('kitty',(-.12,.2,.65));anchor('kitty_shadow',(-.12,.194,.65))
current=station('Studio_Plants')
flower('Entry plant',(-4.4,.13,4.3),.8);flower('Kitchen herbs',(1.4,1.22,-4.3),.45)
# A visible entry, nameplate and two short steps link the house to the village.
current=station('Studio_Entry',role='exit')
box('Front step upper',(1.65,-.06,5.14),(2.05,.22,.6),wood,.075)
box('Front step lower',(1.65,-.27,5.59),(2.25,.18,.58),cream,.075)
box('Welcome mat',(1.65,.16,4.53),(1.75,.04,.74),pink,.1)
box('Mat inner border',(1.65,.185,4.53),(1.55,.015,.56),cream,.07)
# A mesh nameplate is editable and needs no web font or image download.
font=bpy.data.curves.new('Nancy nameplate','FONT');font.body='Nancy';font.align_x='CENTER';font.size=.22;font.extrude=.002
name=bpy.data.objects.new('Nancy welcome lettering',font);collection.objects.link(name);name.parent=current;name.location=cv((1.65,.201,4.58));name.rotation_euler=(0,0,0);font.materials.append(pink)
# Text faces +Z in Blender; horizontal by default, looking up from the mat.
anchor('door',(1.65,.16,4.53));anchor('door_label',(1.65,.42,5.24))
# Earned souvenirs stay separate so the game can preserve each unlock.
current=station('Studio_PicnicMemory',(-2.15,.13,2.7))
box('Basket body',(0,.23,0),(.58,.42,.44),wood,.1)
box('Basket cloth',(0,.46,0),(.6,.05,.46),blush,.035)
tube('Basket handle',[(-.25,.34,0),(-.23,.82,0),(.23,.82,0),(.25,.34,0)],.035,edge)
anchor('picnic',(0,.65,0))
current=station('Studio_LanternMemory',(-3.45,.13,2.5))
box('Lantern base',(0,.05,0),(.34,.08,.31),edge,.035)
box('Lantern light',(0,.3,0),(.23,.43,.22),light,.035)
for x in [-.14,.14]:
    for z in [-.12,.12]:cylinder('Lantern upright',(x,.32,z),.018,.5,edge)
box('Lantern cap',(0,.59,0),(.35,.09,.32),wood,.035)
tube('Lantern handle',[(-.12,.6,0),(-.1,.82,0),(.1,.82,0),(.12,.6,0)],.02,edge)
anchor('lantern',(0,.7,0))
# Additional memory anchors are tied to existing furniture surfaces.
current=station('Studio_Anchors')
for name,pos,yaw in [('ribbon',(2.02,1.24,3.0),0),('letter',(3.38,1.25,2.98),0),('flowers',(-2.3,.145,.55),0),('tea',(-2.7,.78,1.15),0),('frame_wall',(-5.68,2.15,1.65),math.pi/2),('frame_back',(-3.95,2.85,-4.91),0),('frame_nook',(2.9,1.25,2.55),0)]:anchor(name,pos,yaw=yaw)
for i in range(6):anchor('postcard_'+str(i),(-5.68,3.05-(i//3)*.86,-.1+(i%3)*.76),yaw=math.pi/2)
# Simple bedroom wall art, authored as geometry.
current=station('Studio_WallArt')
frame('You are loved print',(-3.95,2.35,-4.91),scale=1.3)

# Export layout data from the real authoring hierarchy, not a second hand-written map.
bpy.context.view_layer.update()
for o in collection.all_objects:
    if 'studio_anchor' in o:
        p=o.matrix_world.translation
        forward=o.matrix_world.to_quaternion()@Vector((0,-1,0))
        anchors[o['studio_anchor']]={'position':[round(p.x,5),round(p.z,5),round(-p.y,5)],'yaw':round(math.atan2(forward.x,-forward.y),6)}
# Camera and lighting are an editable, separate preview collection.
preview=bpy.data.collections.new('PREVIEW — camera and lights (not exported)');scene.collection.children.link(preview)
def light_area(name,webpos,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);preview.objects.link(o);o.location=cv(webpos);o.rotation_euler=(Vector(cv((0,1,0)))-o.location).to_track_quat('-Z','Y').to_euler()
light_area('Soft window light',(-4,10,6),1600,8);light_area('Warm fill',(7,7,3),1100,7);light_area('Back rim',(0,9,-6),1000,6)
cam_data=bpy.data.cameras.new('Studio overview');cam=bpy.data.objects.new('Studio overview',cam_data);preview.objects.link(cam)
cam.location=cv((14,15,19));cam.rotation_euler=(Vector(cv((0,1.5,.2)))-cam.location).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=18.3;scene.camera=cam
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.73,.69,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=96
scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.filepath=str(ROOT/'nancy_studio_home.png')
scene['Studio guide']='Original studio for Nancy. Named stations are editable furniture assemblies. Helpers use browser x/height/depth mapped into Blender Z-up. Camera/lights are excluded from GLB. Re-run this script only to regenerate; save hand edits as a working copy.'
scene['Studio interactions']='Studio_Kitchen -> bake; Studio_Wardrobe -> clothes; Studio_Desk -> Nancy letter; Studio_Bed -> sleepy; Studio_Sofa -> happy pause; Studio_Entry -> village.'
scene['Studio dimensions']='11.6 x 10 browser units; cutaway back/left walls; open middle walking space.'
bpy.context.preferences.filepaths.save_version=0
# Open at a comfortable material view, with the camera showing the complete floor plan.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
blend=ROOT/'nancy_studio_home.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
# Export a separate optimized web copy; the editable source above stays intact.
import runpy
runpy.run_path(str(ROOT/'export_studio_home.py'),run_name='__main__')
