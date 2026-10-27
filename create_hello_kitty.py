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

white = material('Warm porcelain white', (.94, .91, .84))
red = material('Cherry red satin', (.64, .018, .045), .28)
pink = material('Bow seam highlight', (.90, .09, .16))
black = material('Eyes and whiskers', (.009, .006, .012), .32)
yellow = material('Golden yellow nose', (1, .58, .035), .3)
base_mat = material('Rose ceramic pedestal', (.66, .24, .32), .32)
edge_mat = material('Pedestal cream trim', (.95, .72, .56), .35)
floor_mat = material('Blush studio', (.26, .095, .14), .7)

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
head = ellipsoid('Head', (0, 0, 3.18), (1.43, .77, 1.04), white)
parts = [head]
for side in [-1, 1]:
    verts = [(side*.64, -.30, 3.90), (side*1.33, -.24, 3.76),
             (side*1.14, -.13, 4.56), (side*.64, .28, 3.90),
             (side*1.33, .25, 3.76), (side*1.14, .18, 4.56)]
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
smooth.iterations = 6
bpy.ops.object.modifier_apply(modifier=smooth.name)
sub = head.modifiers.new('Silky surface', 'SUBSURF')
sub.levels = 1
for p in head.data.polygons:
    p.use_smooth = True

# The face has the iconic two oval eyes, yellow nose, six whiskers and no mouth.
for side in [-1, 1]:
    ellipsoid('Eye left' if side < 0 else 'Eye right', (side*.51, -.724, 3.25), (.105, .065, .145), black)
ellipsoid('Yellow oval nose', (0, -.787, 3.02), (.145, .075, .098), yellow)
for side in [-1, 1]:
    for i, (z, dz) in enumerate([(3.36, .14), (3.12, 0), (2.90, -.14)]):
        curve(f'Whisker {side} / {i+1}', [(side*1.00, -.56, z), (side*1.36, -.58, z+dz*.5), (side*1.68, -.57, z+dz)], .027, black)

# Short body, rounded dress, little feet, white sleeves and mitten hands.
ellipsoid('Body under dress', (0, .04, 1.69), (.66, .45, .82), white)
for side in [-1, 1]:
    ellipsoid(f'Foot {side}', (side*.40, -.16, .68), (.38, .48, .27), white)
    arm = ellipsoid(f'White arm {side}', (side*.77, -.01, 1.82), (.24, .25, .53), white)
    arm.rotation_euler[1] = side * -.42
    ellipsoid(f'Mitten hand {side}', (side*.95, -.06, 1.52), (.25, .27, .29), white)
    ellipsoid(f'Thumb {side}', (side*.78, -.25, 1.57), (.12, .13, .17), white)
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=.83, radius2=.49, depth=1.12, location=(0, .015, 1.51))
dress = finish(bpy.context.object, 'Red A-line dress', red)
dress.scale.y = .72
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bevel = dress.modifiers.new('Rounded dress hem and neckline', 'BEVEL')
bevel.width = .14
bevel.segments = 6
dress.modifiers.new('Weighted dress normals', 'WEIGHTED_NORMAL')
for side in [-1, 1]:
    ellipsoid(f'Dress shoulder {side}', (side*.52, .015, 1.98), (.25, .30, .25), red)
    ellipsoid(f'Dress button {side}', (side*.26, -.372, 1.95), (.05, .035, .05), yellow)
# A small white collar tucked just beneath the head.
for side in [-1, 1]:
    collar = ellipsoid(f'Peter Pan collar {side}', (side*.19, -.37, 2.13), (.23, .08, .15), white)
    collar.rotation_euler[1] = side * -.28

# The red bow sits on Kitty's left ear (viewer's right).
for side in [-1, 1]:
    loop = ellipsoid(f'Bow loop {side}', (.86+side*.26, -.66, 3.99+side*.075), (.32, .15, .26), red)
    loop.rotation_euler[1] = side * -.32
    inset = ellipsoid(f'Bow folded ribbon {side}', (.86+side*.27, -.789, 3.99+side*.075), (.17, .024, .13), pink)
    inset.rotation_euler[1] = side * -.32
ellipsoid('Bow center knot', (.86, -.81, 3.99), (.17, .13, .185), red)
ellipsoid('Small white tail', (0, .49, 1.17), (.19, .20, .19), white)

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
    ('Key softbox', (-4, -6, 8), 850, 5, (1, .87, .79)),
    ('Fill softbox', (5, -3, 5), 650, 4, (.80, .88, 1)),
    ('Rim softbox', (1, 4, 7), 1100, 3, (1, .65, .70))]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = loc
    aim(obj, (0, 0, 2.2))
bpy.ops.object.camera_add(location=(3.0, -13, 6.0))
camera = bpy.context.object
camera.name = 'Portrait camera'
organize(camera, studio)
aim(camera, (0, 0, 2.25))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 6.35
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = False  # Cloud Blender has no OpenImageDenoise support.
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world.color = (.23, .23, .23)
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
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
