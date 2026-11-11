"""Export an edited nancy_studio_home.blend without changing the source file.
blender -b nancy_studio_home.blend --python-exit-code 1 --python export_studio_home.py
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
blend=Path(bpy.data.filepath)
if not blend.is_file():raise RuntimeError('Open the studio .blend before exporting.')
collection=bpy.data.collections.get('NANCY — studio home')
if not collection:raise RuntimeError('This file is not Nancy’s studio home.')
bpy.context.view_layer.update()
anchors={}
for o in collection.all_objects:
    if 'studio_anchor' in o:
        p=o.matrix_world.translation;f=o.matrix_world.to_quaternion()@Vector((0,-1,0))
        anchors[o['studio_anchor']]={'position':[round(p.x,5),round(p.z,5),round(-p.y,5)],'yaw':round(math.atan2(f.x,-f.y),6)}
# Furniture footprints are measured before mesh reduction. Hanging pieces,
# the floor and the rug do not block a walking character.
obstacles=[]
for name in ['Studio_Bed','Studio_Bedside','Studio_Kitchen','Studio_Sofa','Studio_CoffeeTable','Studio_Wardrobe','Studio_Desk','Studio_Shelf','Studio_Dining','Studio_TeaTray']:
 root=bpy.data.objects.get(name)
 if not root:continue
 parts=[o for o in root.children_recursive if o.type=='MESH' and not (name=='Studio_Desk' and o.name.startswith('Desk stool')) and not (name=='Studio_Dining' and any(p.name.startswith('Dining chair') for p in [o.parent,o.parent.parent] if p))]
 points=[o.matrix_world@Vector(v)for o in parts for v in o.bound_box]
 if not points:continue
 lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)]
 obstacles.append({'name':name,'x':round((lo[0]+hi[0])/2,4),'z':round(-(lo[1]+hi[1])/2,4),'w':round(hi[0]-lo[0],4),'d':round(hi[1]-lo[1],4)})
for label,parts in [('Desk stool',[o for o in collection.all_objects if o.type=='MESH' and o.name.startswith('Desk stool')])]+[(r.name,[o for o in r.children_recursive if o.type=='MESH'])for r in collection.all_objects if r.name.startswith('Dining chair ') and r.type=='EMPTY']:
 points=[o.matrix_world@Vector(v)for o in parts for v in o.bound_box]
 if not points:continue
 lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)]
 obstacles.append({'name':label,'x':round((lo[0]+hi[0])/2,4),'z':round(-(lo[1]+hi[1])/2,4),'w':round(hi[0]-lo[0],4),'d':round(hi[1]-lo[1],4)})
# The bathroom door stays open. Individual fittings block walking, rather
# than treating the whole alcove as a solid inaccessible box.
for label,prefixes in [('Bath screen',['Bathroom front screen','Screen top rail']),('Bath partition',['Bathroom left partition']),('Bath wash cabinet',['Wash cabinet']),('Bath shower',['Shower tray']),('Bath toilet',['Toilet'])]:
 parts=[o for o in collection.all_objects if o.type=='MESH' and any(o.name.startswith(prefix)for prefix in prefixes)]
 points=[o.matrix_world@Vector(v)for o in parts for v in o.bound_box]
 lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)]
 obstacles.append({'name':label,'x':round((lo[0]+hi[0])/2,4),'z':round(-(lo[1]+hi[1])/2,4),'w':round(hi[0]-lo[0],4),'d':round(hi[1]-lo[1],4)})
meshes=[]
for root in [o for o in collection.objects if o.parent is None]:
    parts=[o for o in root.children_recursive if o.type in {'MESH','CURVE','FONT'}]
    if not parts:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.convert(target='MESH')
    parts=[o for o in root.children_recursive if o.type=='MESH' and not (name=='Studio_Desk' and o.name.startswith('Desk stool')) and not (name=='Studio_Dining' and any(p.name.startswith('Dining chair') for p in [o.parent,o.parent.parent] if p))]
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=root.name+'_Mesh'
    # Retain the original high-quality pieces in .blend. The web copy only
    # reduces tiny bevel/curve detail; flat pastel materials need no UV stream.
    if len(o.data.polygons)>600 and root.name!='Studio_Entry':
        dec=o.modifiers.new('Phone export detail','DECIMATE');dec.ratio=.32
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=dec.name)
    meshes.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in collection.all_objects:o.select_set(True)
asset=ROOT/'studio-home.glb'
bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_yup=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False,export_apply=True,export_texcoords=False,export_tangents=False)
triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
meta={'version':1,'title':'Nancy’s cozy studio','source_file':blend.name,'source_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'authoring_script':'create_studio_home.py','script_sha256':hashlib.sha256((ROOT/'create_studio_home.py').read_bytes()).hexdigest(),'export_script':Path(__file__).name,'export_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'asset_bytes':asset.stat().st_size,'triangles':triangles,'mesh_count':len(meshes),'anchors':anchors,'floor':[[-5.8,.13,-5],[5.8,.13,-5],[5.8,.13,5],[-5.8,.13,5]],'framing':[[-6.1,-.65,-5.25],[6.1,-.65,-5.25],[-6.1,-.65,5.3],[6.1,-.65,5.3],[-5.95,4.2,-5.1],[5.95,4.2,-5.1],[-5.95,4.2,5.1],[0,4.3,.65],[.4,-.4,6],[2.9,-.4,6]],'shelf_scale':.28,'navigation':{'radius':.38,'obstacles':obstacles}}
(ROOT/'studio-home.json').write_text(json.dumps(meta,indent=2)+'\n')
print('STUDIO_EXPORTED',asset.stat().st_size,'bytes',triangles,'triangles',len(anchors),'anchors',flush=True)
