"""Fit organic stuffed rabbit ears and a flush satin lining to Silver Bunny.
Uses the existing head/ear controls and keeps all 13 authored performances.
blender -b hello_kitty_plush_bunny.blend --python-exit-code 1 --python refine_silver_bunny.py -- --draft --render
"""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector

SHAPE='rounded-curved-v2'

def mesh_object(name,vertices,faces,material,parent,uvs=None):
    obj=bpy.data.objects.get(name)
    mesh=bpy.data.meshes.new(name+' / fitted surface');mesh.from_pydata(vertices,[],faces);mesh.update()
    if obj:obj.data=mesh
    else:
        obj=bpy.data.objects.new(name,mesh);bpy.data.collections['HELLO KITTY — editable parts'].objects.link(obj)
    obj.parent=parent;obj.matrix_parent_inverse.identity();obj.location=(0,0,0);obj.rotation_euler=(0,0,0);obj.scale=(1,1,1)
    mesh.materials.append(material)
    for face in mesh.polygons:face.use_smooth=True
    uv=mesh.uv_layers.new(name='Packed fleece UV')
    for face in mesh.polygons:
        for loop in face.loop_indices:
            point=mesh.vertices[mesh.loops[loop].vertex_index].co
            uv.data[loop].uv=(point.x*2,point.z*2)
    obj['plush_surface']='close-cropped-fleece';obj['plush_ear_shape']=SHAPE
    return obj

def center(t,sign):
    # Both roots are buried in the hood. The left tip leans outward, while
    # the right is slightly shorter with a soft forward bend.
    return Vector((sign*(.70+(.39 if sign<0 else .27)*t*t),.035-(.13 if sign<0 else .27)*t**3,4.19+(1.62 if sign<0 else 1.56)*t-.045*t**5))

def surface(t,theta,sign):
    c=center(t,sign)
    tangent=(center(min(1,t+.001),sign)-center(max(0,t-.001),sign)).normalized()
    across=Vector((tangent.z,0,-tangent.x)).normalized()
    front=tangent.cross(across).normalized()
    # Broad padded ear with an explicit elliptical end cap, rather than a
    # leaf-like taper all the way to a pointed tip.
    if t<=.78:
        width=.235+.070*math.sin(math.pi*t/.78)
    else:
        width=.235*math.sqrt(max(0,1-((t-.78)/.22)**2))
    return c+across*(width*math.cos(theta))+front*(width*.74*math.sin(theta))

def refine_silver_bunny():
    scene=bpy.context.scene
    if scene.get('plush_variant')!='bunny' or scene.get('plush_ear_shape')==SHAPE:return
    scene.frame_set(1);head=bpy.data.objects['CTRL_Head'];cream=bpy.data.materials['Plush cream fabric']
    # A rabbit hood has a clean oval face; remove the old embedded cat-ear nubs.
    old=bpy.data.objects['Head'];world=old.matrix_world.copy()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=(0,0,3.4))
    temporary=bpy.context.object;temporary.scale=(1.55,1.04,1.16)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    old.data=temporary.data.copy();bpy.data.objects.remove(temporary,do_unlink=True)
    old.matrix_world=world;old.data.materials.clear();old.data.materials.append(cream)
    for modifier in list(old.modifiers):old.modifiers.remove(modifier)
    for face in old.data.polygons:face.use_smooth=True
    for uv in old.data.uv_layers.active.data:uv.uv*=4
    old['plush_hood_surface']=SHAPE
    # A second shell at nearly the same depth makes a stray rim near the
    # rabbit-ear bases. The clean oval head itself is the hood surface.
    hood=bpy.data.objects.get('Plush bunny hood')
    if hood:bpy.data.objects.remove(hood,do_unlink=True)
    lining=cream.copy();lining.name='Bunny soft silver satin lining'
    bs=lining.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.65,.69,.74,1)
    bs.inputs['Metallic'].default_value=.08;bs.inputs['Roughness'].default_value=.83;bs.inputs['Sheen Weight'].default_value=.16
    lining.diffuse_color=(.65,.69,.74,1)
    for node in lining.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.24
    for sign in [-1,1]:
        control=bpy.data.objects['CTRL_Plush_Ear_'+str(sign)]
        root=center(0,sign);control.location=head.matrix_world.inverted()@root
        control.rotation_euler=(0,0,0);bpy.context.view_layer.update()
        inverse=control.matrix_world.inverted()
        # Closed stuffed ear, with a round tapered tip and a wide sewn base.
        rings=48;segments=40;vertices=[];faces=[]
        for k in range(rings):
            t=.5-.5*math.cos(math.pi*k/rings)
            for j in range(segments):vertices.append(inverse@surface(t,j*math.tau/segments,sign))
        tip=len(vertices);vertices.append(inverse@center(1,sign));base=len(vertices);vertices.append(inverse@root)
        for k in range(rings-1):
            for j in range(segments):
                a=k*segments+j;b=k*segments+(j+1)%segments
                faces.append((a,b,b+segments,a+segments))
        for j in range(segments):
            faces.append((base,(j+1)%segments,j));faces.append(((rings-1)*segments+j,(rings-1)*segments+(j+1)%segments,tip))
        outer=mesh_object('Bunny long ear '+str(sign),vertices,faces,cream,control)
        outer['plush_ear_role']='stuffed-outer';outer['plush_ear_side']=sign
        # Thin oval fabric panel follows the actual curved front surface.
        vertices=[inverse@(surface(.16,-math.pi/2,sign)+Vector((0,-.006,0)))];faces=[]
        rows=26;across=16
        for row in range(1,rows):
            s=row/rows;t=.16+.69*s;spread=.67*math.sqrt(max(0,1-(2*s-1)**2))
            for j in range(across+1):
                theta=-math.pi/2+spread*(2*j/across-1)
                vertices.append(inverse@(surface(t,theta,sign)+Vector((0,-.006,0))))
        top=len(vertices);vertices.append(inverse@(surface(.85,-math.pi/2,sign)+Vector((0,-.006,0))))
        for j in range(across):faces.append((0,2+j,1+j))
        for row in range(rows-2):
            for j in range(across):
                a=1+row*(across+1)+j;faces.append((a,a+1,a+across+2,a+across+1))
        for j in range(across):
            a=1+(rows-2)*(across+1)+j;faces.append((a,a+1,top))
        inner=mesh_object('Bunny silver inner ear '+str(sign),vertices,faces,lining,control)
        inner['plush_ear_role']='flush-lining';inner['plush_ear_side']=sign
        # Independent small settling beats; the sewn roots remain fixed.
        control.animation_data_clear()
        for frame in range(1,50,2):
            t=(frame-1)/48;envelope=math.sin(math.pi*t)**2
            control.rotation_euler=(.014*math.sin(t*math.tau*2+sign*.35)*envelope,sign*.021*math.sin(t*math.tau-sign*.25)*envelope,.006*math.sin(t*math.tau)*envelope)
            control.keyframe_insert('rotation_euler',frame=frame)
        for frame in [49,50,727]:
            control.rotation_euler=(0,0,0);control.keyframe_insert('rotation_euler',frame=frame)
        for fc in control.animation_data.action.fcurves:
            for key in fc.keyframe_points:key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
    scene['plush_ear_shape']=SHAPE;scene.frame_set(1);bpy.context.view_layer.update()
    print('SILVER_BUNNY_EARS_READY',SHAPE,flush=True)

if __name__=='__main__':
    refine_silver_bunny();draft='--draft'in sys.argv
    path=Path('/tmp/silver-bunny-fitted.blend')if draft else Path(bpy.data.filepath)
    bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.render.filepath='//hello_kitty_plush_bunny.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    if '--render'in sys.argv:
        bpy.context.scene.render.filepath='/tmp/silver-bunny-fitted.png'if draft else'//hello_kitty_plush_bunny.png'
        bpy.ops.render.render(write_still=True)
