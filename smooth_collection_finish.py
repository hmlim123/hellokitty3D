"""Apply Nancy's smooth matte finish to the five existing character editions.
Preserves the original smooth forms, morphs, sockets, ear fitting and all clips.
blender -b hello_kitty_plush_cloud.blend --python-exit-code 1 --python smooth_collection_finish.py -- --draft --render
"""
import bpy,sys
from pathlib import Path

FINISH='smooth-matte'

def restore_smooth_surface(reference):
    # Read only vertex positions from the pre-fleece project. Do not replace
    # objects, materials, parenting, animation or the newly fitted rabbit ears.
    scene=bpy.context.scene
    if scene.get('plush_microrelief_removed'):return
    live={o.name:o for o in bpy.data.collections['HELLO KITTY — editable parts'].objects if o.type=='MESH' and o.get('plush_surface')}
    before=set(bpy.data.objects)
    with bpy.data.libraries.load(str(reference),link=False) as (available,loaded):
        names=[name for name in live if name in available.objects]
        loaded.objects=list(names)
    restored=[]
    for name,source in zip(names,loaded.objects):
        target=live[name]
        if not source or source.type!='MESH' or len(source.data.vertices)!=len(target.data.vertices):continue
        if target.get('plush_ear_shape') or target.get('plush_hood_surface'):continue
        a,b=target.data,source.data
        for vertex,original in zip(a.vertices,b.vertices):vertex.co=original.co
        if a.shape_keys:
            if not b.shape_keys or set(a.shape_keys.key_blocks.keys())!=set(b.shape_keys.key_blocks.keys()):continue
            for key in a.shape_keys.key_blocks:
                old=b.shape_keys.key_blocks[key.name]
                for vertex,original in zip(key.data,old.data):vertex.co=original.co
        a.update();restored.append(name)
    for obj in set(bpy.data.objects)-before:bpy.data.objects.remove(obj,do_unlink=True)
    scene['plush_microrelief_removed']=True
    print('ORIGINAL_SMOOTH_SURFACES_RESTORED',restored,flush=True)

def smooth_collection_finish():
    scene=bpy.context.scene
    if scene.get('plush_surface')==FINISH:return
    character=bpy.data.collections['HELLO KITTY — editable parts']
    materials={mat for obj in character.objects if obj.type in ['MESH','CURVE'] for mat in obj.data.materials if mat}
    for mat in materials:
        if not mat.use_nodes:continue
        nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF')
        if not bs:continue
        fabric=any(n.type in ['NORMAL_MAP','BUMP','TEX_IMAGE'] for n in nodes)
        if fabric:
            for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
            for node in list(nodes):
                if node.type in ['NORMAL_MAP','BUMP','TEX_IMAGE']:nodes.remove(node)
            bs.inputs['Roughness'].default_value=.76 if mat.name.startswith('Bunny soft silver') else .62
            bs.inputs['Sheen Weight'].default_value=.06
            bs.inputs['Specular IOR Level'].default_value=.18
            mat['surface_finish']=FINISH
        elif mat.name=='Plush silver satin':
            bs.inputs['Metallic'].default_value=.22;bs.inputs['Roughness'].default_value=.50
        elif mat.name=='Plush cocoa embroidery':
            bs.inputs['Roughness'].default_value=.50
    for obj in character.objects:
        if obj.get('plush_surface'):obj['plush_surface']=FINISH
    scene['plush_microrelief_removed']=True
    scene['plush_surface']=FINISH
    scene['plush_guide']='Smooth matte finish without fleece normal or bump textures. All 13 named performances, fitted Silver Bunny ears, paw morphs and sockets retained. Dance 1–49; wave/wink 49–97; happy 391–451 at 24 fps.'
    scene.frame_set(1);print('SMOOTH_COLLECTION_FINISH_READY',scene['plush_variant'],flush=True)

if __name__=='__main__':
    if '--reference'in sys.argv:restore_smooth_surface(sys.argv[sys.argv.index('--reference')+1])
    smooth_collection_finish();style=bpy.context.scene['plush_variant'];draft='--draft'in sys.argv
    path=Path('/tmp')/('kitty-smooth-'+style+'.blend')if draft else Path(bpy.data.filepath)
    bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.render.filepath='//hello_kitty_plush_'+style+'.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    if '--render'in sys.argv:
        bpy.context.scene.render.filepath='/tmp/kitty-smooth-'+style+'.png'if draft else'//hello_kitty_plush_'+style+'.png'
        bpy.ops.render.render(write_still=True)
