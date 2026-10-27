"""Generate an editable Hello Kitty scene. Blender 4.3+; no external assets.
Run: blender --background --python create_hello_kitty.py -- --render
"""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):
    bpy.data.materials.remove(data)


def material(name, color, roughness=.4):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return m

white = material('Warm porcelain white', (1, .96, .89))
red = material('Strawberry pink satin', (.83, .15, .28), .38)
pink = material('Ribbon fold rose', (.52, .055, .12))
black = material('Eyes and whiskers', (.008, .004, .006), 1)
# Printed ink eyes and whiskers: dark even under bright lights, with no shiny dots.
ink = black.node_tree.nodes.get('Principled BSDF')
ink.inputs['Specular IOR Level'].default_value = 0
ink.inputs['Emission Color'].default_value = (.008, .004, .006, 1)
ink.inputs['Emission Strength'].default_value = .7
yellow = material('Golden yellow nose', (1, .58, .035), .3)
base_mat = material('Rose ceramic pedestal', (.82, .39, .46), .45)
edge_mat = material('Pedestal cream trim', (.95, .72, .56), .35)
floor_mat = material('Blush studio', (.95, .54, .66), .8)
# Uniform luminous paper background: keep the top of the frame pastel, too.
background_shader=floor_mat.node_tree.nodes.new('ShaderNodeEmission')
background_shader.inputs['Color'].default_value=(.95,.38,.58,1)
background_shader.inputs['Strength'].default_value=1
floor_mat.node_tree.links.new(background_shader.outputs[0],floor_mat.node_tree.nodes.get('Material Output').inputs['Surface'])
porcelain=white.node_tree.nodes.get('Principled BSDF')
porcelain.inputs['Emission Color'].default_value=(1,.96,.89,1)
porcelain.inputs['Emission Strength'].default_value=.20

green = material('Fresh sage stems', (.16, .34, .17), .5)
leaf_green = material('Soft green leaves', (.28, .48, .24), .5)
flower_pink = material('Petal pink', (.98, .30, .45), .48)
flower_yellow = material('Butter yellow petals', (1, .72, .12), .48)

character = bpy.data.collections.new('HELLO KITTY — editable parts')
bpy.context.scene.collection.children.link(character)
studio = bpy.data.collections.new('STUDIO — lights and display')
bpy.context.scene.collection.children.link(studio)


def organize(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def finish(obj, name, mat, coll=character):
    obj.name = name
    obj.data.materials.append(mat)
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True
    organize(obj, coll)
    return obj


def ellipsoid(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat)


def curve(name, points, radius, mat):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 5
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for p, co in zip(spline.bezier_points, points):
        p.co = co
        p.handle_left_type = 'AUTO'
        p.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    character.objects.link(obj)
    data.materials.append(mat)
    return obj

# Soft triangular ears merge with the head into a single smooth sculpt.
head = ellipsoid('Head', (0, 0, 3.40), (1.55, 1.04, 1.16), white)
parts = [head]
for side in [-1, 1]:
    verts = [(side*.70, -.53, 4.03), (side*1.47, -.44, 3.98),
             (side*1.20, -.31, 4.83), (side*.70, .52, 4.03),
             (side*1.47, .44, 3.98), (side*1.20, .29, 4.83)]
    mesh = bpy.data.meshes.new('Rounded triangular ear')
    mesh.from_pydata(verts, [], [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)])
    mesh.update()
    obj = bpy.data.objects.new('Ear', mesh)
    character.objects.link(obj)
    parts.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.join()
remesh = head.modifiers.new('Unified soft ear silhouette', 'REMESH')
remesh.mode = 'VOXEL'
remesh.voxel_size = .035
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth = head.modifiers.new('Soft sculpt surface', 'SMOOTH')
smooth.factor = 1.1
smooth.iterations = 14
bpy.ops.object.modifier_apply(modifier=smooth.name)
sub = head.modifiers.new('Silky surface', 'SUBSURF')
sub.levels = 1
for p in head.data.polygons:
    p.use_smooth = True

# Broad, low-set face leaves lots of soft forehead and cheek volume.
# Thin, curved black patches follow the rounded cheek surface like printed eyes.
for side in [-1, 1]:
    cx=side*.63; cz=3.27
    verts=[]
    for radius in [0,.25,.5,.75,1]:
        for j in range(64):
            t=2*math.pi*j/64
            x=cx+.119*radius*math.cos(t); z=cz+.172*radius*math.sin(t)
            y=-1.04*math.sqrt(max(.01,1-(x/1.55)**2-((z-3.4)/1.16)**2))-.014
            verts.append((x,y,z))
    faces=[]
    for ring in range(4):
        for j in range(64):
            a=ring*64+j;b=ring*64+(j+1)%64
            faces.append((a,b,b+64,a+64))
    mesh=bpy.data.meshes.new('Printed oval eye surface')
    mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('Eye left' if side<0 else 'Eye right',mesh)
    character.objects.link(o);o.data.materials.append(black)
    for poly in mesh.polygons:poly.use_smooth=True
ellipsoid('Yellow oval nose', (0, -1.005, 3.06), (.15, .075, .103), yellow)
for side in [-1, 1]:
    for i, (z, dz) in enumerate([(3.40, .06), (3.12, -.045), (2.87, -.15)]):
        curve(f'Whisker {side} / {i+1}', [(side*1.26, -.58, z), (side*1.55, -.63, z+dz*.5), (side*1.83, -.61, z+dz)], .035, black)

# A full, softly rounded dress made from elliptical rings, closed at both ends.
# More depth through the tummy and a rolled-under hem create a toy-like silhouette.
rings = [(1.00,.83,.61),(1.04,.98,.72),(1.14,1.035,.77),
         (1.30,1.01,.79),(1.55,.94,.78),(1.80,.82,.71),
         (2.02,.71,.63),(2.22,.62,.53),(2.32,.48,.42)]
verts = []
for z, rx, ry in rings:
    for j in range(96):
        angle = 2*math.pi*j/96
        verts.append((rx*math.cos(angle), .04+ry*math.sin(angle), z))
faces = []
for i in range(len(rings)-1):
    for j in range(96):
        a=i*96+j; b=i*96+(j+1)%96
        faces.append((a,b,b+96,a+96))
faces.extend([tuple(reversed(range(96))),tuple(range((len(rings)-1)*96,len(rings)*96))])
mesh=bpy.data.meshes.new('Full rounded dress mesh')
mesh.from_pydata(verts, [], faces)
mesh.update()
dress=bpy.data.objects.new('Strawberry pink rounded dress',mesh)
character.objects.link(dress)
dress.data.materials.append(red)
for poly in mesh.polygons:
    poly.use_smooth=True
dress.modifiers.new('Soft tailored volume','SUBSURF').levels=2
for side in [-1, 1]:
    ellipsoid(f'Foot {side}', (side*.44, -.24, .72), (.43, .59, .31), white)
    pieces=[
        ellipsoid('arm upper',(side*.77,-.39,2.03),(.24,.27,.32),white),
        ellipsoid('arm elbow',(side*.76,-.63,1.85),(.25,.27,.24),white),
        ellipsoid('mitten palm',(side*.59,-.84,1.84),(.27,.27,.29),white),
        ellipsoid('soft thumb',(side*.40,-.87,1.98),(.12,.16,.15),white)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in pieces:o.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0]
    bpy.ops.object.join()
    arm=bpy.context.object;arm.name=f'White arm {side}'
    remesh=arm.modifiers.new('Continuous mitten silhouette','REMESH')
    remesh.mode='VOXEL';remesh.voxel_size=.023
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    soft=arm.modifiers.new('Soft mitten transitions','SMOOTH')
    soft.factor=1;soft.iterations=10
    bpy.ops.object.modifier_apply(modifier=soft.name)
    arm.modifiers.new('Smooth mitten surface','SUBSURF').levels=1
    for poly in arm.data.polygons:poly.use_smooth=True
    ellipsoid(f'Pink shoulder {side}', (side*.58, -.02, 2.20), (.27,.38,.25), red)

# Chunky bow: two plump, diagonally arranged loops and a spherical central knot.
for side in [-1, 1]:
    x=1.01+side*.30
    z=4.27-side*.16
    loop=ellipsoid(f'Bow loop {side}', (x, -.72, z), (.37,.29,.43), red)
    loop.rotation_euler[1]=-.45
    # Recess-colored folds, nestled against the knot, emphasize ribbon thickness.
    fold=ellipsoid(f'Bow folded ribbon {side}', (1.01+side*.21, -.989, 4.27-side*.10), (.115,.027,.15), pink)
    fold.rotation_euler[1]=-.45
ellipsoid('Bow center knot', (1.01, -1.04, 4.27), (.25,.23,.25), red)
ellipsoid('Small white tail', (0, .75, 1.28), (.24,.25,.24), white)

# A little bouquet with dimensional petals, raised centers and curved stems.
curve('Pink flower stem', [(-.22,-1.13,1.04),(-.12,-1.18,1.59),(-.30,-1.15,2.30)], .045, green)
curve('Yellow flower stem', [(.21,-1.09,1.04),(.06,-1.16,1.60),(.31,-1.13,2.52)], .045, green)
for name, cx, cy, cz, mat, radius in [
    ('Pink daisy',-.33,-1.23,2.31,flower_pink,.27),
    ('Yellow daisy',.29,-1.18,2.61,flower_yellow,.245)]:
    for i in range(5):
        angle=2*math.pi*i/5
        obj=ellipsoid(f'{name} petal {i+1}',
                      (cx+radius*math.sin(angle),cy,cz+radius*math.cos(angle)),
                      (.18,.155,.245),mat)
        obj.rotation_euler[1]=angle
    ellipsoid(f'{name} center rim', (cx,cy-.125,cz),(.183,.075,.183),white if cx<0 else yellow)
    ellipsoid(f'{name} golden center', (cx,cy-.185,cz),(.125,.07,.125),yellow)
for side in [-1,1]:
    leaf=ellipsoid(f'Bouquet leaf {side}', (side*.25,-1.12,1.86),(.30,.075,.13),leaf_green)
    leaf.rotation_euler[1]=side*-.4
    curve(f'Leaf vein {side}', [(side*.04,-1.20,1.79),(side*.24,-1.20,1.85),(side*.43,-1.16,1.94)], .014, green)

# Circular display pedestal, seamless backdrop, and softbox lighting.
for name, radius, depth, z, mat in [('Rose display plinth', 2.15, .30, .20, base_mat), ('Cream rim', 2.17, .055, .36, edge_mat)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=radius, depth=depth, location=(0, 0, z))
    obj = finish(bpy.context.object, name, mat, studio)
    bevel = obj.modifiers.new('Soft display edge', 'BEVEL')
    bevel.width = .065 if depth > .1 else .02
    bevel.segments = 4
    obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, .025))
finish(bpy.context.object, 'Infinite blush floor', floor_mat, studio)


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z', 'Y').to_euler()


for name, loc, power, size, color in [
    ('Key softbox', (-4, -6, 8), 1000, 5, (1, .91, .84)),
    ('Fill softbox', (5, -3, 5), 950, 5, (1, .90, .94)),
    ('Rim softbox', (1, 4, 7), 1100, 3, (1, .65, .70))]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.use_shadow = False  # Clean pastel illustration lighting: no stochastic shadow speckles.
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = loc
    aim(obj, (0, 0, 2.2))
bpy.ops.object.camera_add(location=(2.8, -14, 6.0))
camera = bpy.context.object
camera.name = 'Portrait camera'
organize(camera, studio)
aim(camera, (0, -.05, 2.45))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 6.4
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 32
scene.eevee.use_raytracing = False
scene.eevee.use_fast_gi = False
scene.eevee.use_shadows = False
# Deliberately shadow-free toy/postcard lighting avoids stochastic shadow dots.
# A solid pastel oval underfoot keeps a grounded, vintage illustration look.
shadow_mat=material('Warm pastel standing oval',(.72,.43,.40),1)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1,depth=.006,location=(0,0,.394))
mat_obj=finish(bpy.context.object,'Pastel oval standing mat',shadow_mat,studio)
mat_obj.scale=(1.18,.78,1)

scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world.color = (.55, .48, .45)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium Low Contrast'
scene.view_settings.exposure = .45
scene.render.image_settings.file_format = 'PNG'
bpy.context.preferences.filepaths.save_version = 0
scene.render.filepath = str(OUT / 'hello_kitty_preview.png')
# Open in an uncluttered material-colored viewport facing the character.
bpy.ops.object.select_all(action='DESELECT')
head.select_set(True)
bpy.context.view_layer.objects.active = head
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.color_type = 'MATERIAL'
scene['Model notes'] = 'Stylized Hello Kitty fan model. Separate editable parts; studio collection can be hidden. No external textures or add-ons.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'hello_kitty.blend'))
if '--render' in sys.argv:
    bpy.ops.render.render(write_still=True)
print('HELLO_KITTY_BUILD_COMPLETE')
