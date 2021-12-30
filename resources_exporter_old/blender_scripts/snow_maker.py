import bpy
import bmesh 
from mathutils import *

def get_items_w_type(lst, of_type):
    return [e for e in lst if isinstance(e, of_type)]

def extrude_faces(bm, faces=None, direction=Vector((0,0,1))):
    if faces is None: faces = bm.faces[:]
#    r = bmesh.ops.extrude_face_region(bm, geom=faces)
    r = bmesh.ops.extrude_discrete_faces(bm, faces=faces)
    
#    geom = r['geom']
#    verts = get_items_w_type(geom, bmesh.types.BMVert)
#    faces = get_items_w_type(geom, bmesh.types.BMFace)
    
    faces = r['faces']
    verts = [v for f in faces for v in f.verts]
    
    bmesh.ops.translate(bm, vec = direction, verts=verts)
    bpy.ops.mesh.select_all(action='DESELECT')
    for f in faces:
        f.select=True
    
    bpy.ops.mesh.remove_doubles()
    
def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    return mat

def add_material_to_obj(obj, mat):
    def find_mat():
        return obj.data.materials.find(mat.name)
    if find_mat()==-1:
        obj.data.materials.append(mat)
    return find_mat()

def apply_material_to_faces(faces, mat_id):
    for f in faces:
        f.material_index = mat_id

def select_faces_normal_treshold(bm, treshold=0.5, n_coord=2):
    s_faces = []
    for f in bm.faces:
        if f.normal[n_coord] > treshold:
            f.select = True
            s_faces.append(f)
    return s_faces

def make_snow(obj):
    bpy.ops.ed.undo_push()
    
    bm = bmesh.from_edit_mesh(obj.data)
    
    mat_name = "snow"
    mat = get_or_create_material(mat_name)
    
    faces = select_faces_normal_treshold(bm, 0.5, 2)
    
    mat_id = add_material_to_obj(obj, mat)
    apply_material_to_faces(faces, mat_id)
    
    extrude_faces(bm, faces, Vector((0,0,0.1)))
    
    bmesh.update_edit_mesh(obj.data)
    
    
obj = bpy.context.active_object
# obj = bpy.context.scene.objects['Cube']
make_snow(obj)