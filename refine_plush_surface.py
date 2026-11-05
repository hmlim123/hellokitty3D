"""Close-cropped fleece correction: no exposed curl geometry or chin fringe.
Import refine_surface(style) from the collection builder, or run this script
against an existing plush .blend with -- --style cloud [--draft] [--render].
"""
import bpy, math, sys
import numpy as np
from mathutils import Vector
from pathlib import Path

def normal_image():
    size=512;rng=np.random.default_rng(7314);h=np.zeros((size,size),dtype=np.float32)
    count=9000;x=rng.uniform(0,size,count);y=rng.uniform(0,size,count)
    angle=rng.uniform(0,math.tau,count);length=rng.uniform(3.5,8,count);bend=rng.uniform(-1.3,1.3,count)
    amplitude=rng.uniform(.55,1,count)
    for phase in np.linspace(0,1,8):
        px=x+np.cos(angle)*length*phase-np.sin(angle)*bend*np.sin(phase*math.pi)
        py=y+np.sin(angle)*length*phase+np.cos(angle)*bend*np.sin(phase*math.pi)
        for dx in range(-2,3):
            for dy in range(-2,3):
                weight=amplitude*np.exp(-(dx*dx+dy*dy)/1.3)
                np.add.at(h,((np.rint(py).astype(int)+dy)%size,(np.rint(px).astype(int)+dx)%size),weight)
    # Seamless, densely overlapping fibers, with no large isolated curls.
    h=(h+np.roll(h,1,0)+np.roll(h,-1,0)+np.roll(h,1,1)+np.roll(h,-1,1))/5
    lo,hi=np.percentile(h,[1,99]);h=np.clip((h-lo)/max(.001,hi-lo),0,1)
    nx=(np.roll(h,1,1)-np.roll(h,-1,1))*.7
    ny=(np.roll(h,1,0)-np.roll(h,-1,0))*.7
    nz=np.ones_like(h);norm=np.sqrt(nx*nx+ny*ny+nz*nz)
    rgba=np.stack((nx/norm*.5+.5,ny/norm*.5+.5,nz/norm*.5+.5,np.ones_like(h)),axis=-1)
    image=bpy.data.images.new('Packed close-cropped fleece normal',width=size,height=size)
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.astype(np.float32).ravel());image.pack()
    return image

def refine_surface(style):
    s=bpy.context.scene
    if s.get('plush_surface')=='close-cropped-fleece':return
    s.frame_set(1);char=bpy.data.collections['HELLO KITTY — editable parts']
    for obj in list(char.objects):
        if obj.name.startswith(('Plush pile ','Plush rounded ear ','Kitten pink inner ear ')):
            bpy.data.objects.remove(obj,do_unlink=True)
    # The costume opening hugs the head instead of hanging below the chin.
    hood=bpy.data.objects.get('Plush '+style+' hood')
    if hood:
        bpy.ops.object.select_all(action='DESELECT');hood.select_set(True);bpy.context.view_layer.objects.active=hood
        sub=hood.modifiers.new('Soft fitted hood opening','SUBSURF');sub.levels=1
        bpy.ops.object.modifier_apply(modifier=sub.name)
        wrap=hood.modifiers.new('Hood fitted to stuffed head','SHRINKWRAP')
        wrap.target=bpy.data.objects['Head'];wrap.wrap_method='NEAREST_SURFACEPOINT';wrap.offset=.015
        bpy.ops.object.modifier_apply(modifier=wrap.name)
    image=normal_image();fabrics=set()
    for obj in char.objects:
        if obj.type!='MESH':continue
        for mat in obj.data.materials:
            if not mat or not mat.use_nodes:continue
            if any(n.type=='TEX_IMAGE' and n.image and 'plush' in n.image.name.lower() for n in mat.node_tree.nodes):fabrics.add(mat)
    for mat in fabrics:
        bs=mat.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Roughness'].default_value=.96
            bs.inputs['Sheen Weight'].default_value=.10
            bs.inputs['Specular IOR Level'].default_value=.12
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE':node.image=image
            if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.42
    # Keep the original smooth mesh and paw morphs; the final matte pass
    # removes these intermediate fabric normals without geometric microrelief.
    for obj in char.objects:
        if obj.type!='MESH' or not any(m in fabrics for m in obj.data.materials):continue
        if obj.name.startswith(('Eye ','Kitten eye','Baby embroidered','Baby duck')):continue
        obj['plush_surface']='close-cropped-fleece'
        mesh=obj.data
        if mesh.uv_layers.active:
            for uv in mesh.uv_layers.active.data:uv.uv*=.5
        mesh.update()
    # Embroidered whiskers lie on the cheek, inside its silhouette. They are
    # distinct from the removed white fringe and do not stick out like rods.
    for sign in [-1,1]:
        for i,(z,dz) in enumerate([(3.42,.045),(3.17,-.01),(2.96,-.065)]):
            obj=bpy.data.objects.get(f'Whisker {sign} / {i+1}')
            if not obj:continue
            inverse=obj.matrix_world.inverted();obj.data.bevel_depth=.013;obj.data.bevel_resolution=2
            for j,bp in enumerate(obj.data.splines[0].bezier_points):
                t=j/max(1,len(obj.data.splines[0].bezier_points)-1);x=sign*(1.04+.34*t);zz=z+dz*t
                yy=-1.04*math.sqrt(max(.02,1-(x/1.55)**2-((zz-3.4)/1.16)**2))-.025
                bp.co=inverse@Vector((x,yy,zz));bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
            obj['plush_embroidery']=True
    s['plush_surface']='close-cropped-fleece'
    s['plush_guide']='Close-cropped fleece with packed seamless normal texture; no loose chin fibers. 13 named motions. Dance 1–49; wave/wink 49–97; happy expression 391–451. Stitched cheek whiskers; fused paw morphs preserved.'
    s.frame_set(1)
    print('NATURAL_PLUSH_SURFACE_READY',style,flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else[]
    style=args[args.index('--style')+1]if '--style'in args else bpy.context.scene['plush_variant']
    refine_surface(style)
    path=Path('/tmp')/('plush-natural-'+style+'.blend')if '--draft'in args else Path(bpy.data.filepath)
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene.render.filepath='//hello_kitty_plush_'+style+'.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    if '--render'in args:
        bpy.context.scene.render.filepath='/tmp/plush-natural-'+style+'.png'if '--draft'in args else'//hello_kitty_plush_'+style+'.png'
        bpy.ops.render.render(write_still=True)
