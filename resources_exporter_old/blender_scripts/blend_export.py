# blender "/home/hermit/Dropbox/under_standing/resources/models/tech/refrigerator.blend" --background --python "resource_processor.py" "/test_output"

import bpy
import sys
import os
from math import *
from pathlib import Path
from mathutils import Vector
dir = os.path.dirname(bpy.data.filepath)
sys.path.append(__file__[:__file__.rfind("/")+1])

import godot_generator

import importlib
importlib.reload(godot_generator)

from godot_generator import ResourcesGenerator

scene = bpy.context.scene

output_folder:Path = Path(sys.argv[-2]).resolve()
game_root = Path(sys.argv[-1]).resolve()
resource_folder = Path(output_folder.as_posix()[len(game_root.as_posix())+1:])
print(game_root)
print(resource_folder)
resources_generator = ResourcesGenerator(game_root)

def generate_mesh_resource(object_data):
    resources_generator.generate_mesh(object_data.copy())

def generate_collision_shape_resource(object_data):
    resources_generator.generate_collision_shape(object_data.copy())

def generate_body_resource(type, object_data):
    resources_generator.generate_body(type, object_data.copy())

def export_selected_objects(filepath:Path, model):
    if model["properties"]["format"] == "obj":
        bpy.ops.export_scene.obj(
            filepath=filepath.as_posix(),
            check_existing=False,
            use_selection=True,
            use_triangles=True,
            axis_forward='-Z', 
            axis_up='Y')
    
    elif model["properties"]["format"] == "glb":
        bpy.ops.export_scene.gltf(
            filepath=filepath.as_posix(),
            check_existing=False,
            use_selection=True)

def format_modelname(model_name):
    if model_name[-4:] == "_ref": model_name = model_name[:-4]
    return model_name

def unselect_all_objects():
    for collection in bpy.context.scene.collection.children.values():
        for obj in collection.objects.values():
            obj.select_set(False)
            obj.hide_set(False)

def get_vertex_data(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    points = []
    for vert_loop in mesh.loop_triangles:
        for vert_id in vert_loop.vertices:
            vert = mesh.vertices[vert_id].co
            points+=[
                vert[0]*obj.scale[0]+obj.location[0], 
                vert[2]*obj.scale[2]+obj.location[2], 
                -vert[1]*obj.scale[1]-obj.location[1]]

    return points

def get_bool_property(object, key):
    if key in object:
        return object[key]==1
    return False

def get_property(object, key, default):
    if key in object:
        return object[key]
    return default

def fill_object_properties(model, obj):
    props = model["properties"]
    for property_key in props.keys():
        value = props[property_key]
        if type(value) == bool:
            props[property_key] = value or get_bool_property(obj, property_key)
        else:
            props[property_key] = get_property(obj, property_key, value)


def render_icon(model):
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 8
    scene.render.resolution_x = model["properties"]["icon_size"]
    scene.render.resolution_y = model["properties"]["icon_size"]
    scene.camera.location[0] = 1
    scene.camera.location[1] = -1
    scene.camera.location[2] = 1 + model["properties"]["camera_look_at_z"]
    scene.camera.data.type = "ORTHO"
    scene.camera.data.ortho_scale = model["properties"]["ortho_scale"]
    scene.camera.rotation_euler[0] = pi/4
    scene.camera.rotation_euler[1] = 0
    scene.camera.rotation_euler[2] = pi/4
    scene.render.film_transparent = True
    scene.render.filepath = (output_folder / (model["name"] + "_icon.png")).as_posix()
    bpy.ops.render.render(write_still=True)

def string_starts_with(string, match):
    if len(string)<len(match): return False
    else:
        return string[:len(match)] == match

def get_name_without_dot(name):
    dot_pos = name.rfind(".")
    if dot_pos!=-1:
        return name[:dot_pos]
    else: return name

def matrix4x4_to_list(matrix):
    l = []
    for y in range(4):
        for x in range(4):
            l.append(matrix[y][x])
    return l
    
def rotate_vector(vec, rot):
    vec.rotate(rot)
    return vec

def swap_yz(vec):
    vec.y, vec.z = vec.z, vec.y
    return vec

def get_godot_transform_of_obj(obj):
    def vector_to_basis(vec, obj):
        return list(swap_yz(rotate_vector(vec, obj.rotation_euler)))
    
    basis_x = vector_to_basis(Vector((1,0,0)), obj)
    basis_y = vector_to_basis(Vector((0,0,1)), obj)
    basis_z = vector_to_basis(Vector((0,1,0)), obj)
    origin = list(swap_yz(obj.location))

    return basis_x + basis_y + basis_z + origin


def scan_object_for_model(obj, model):
    obj.select_set(True)
    material_names = obj.material_slots.keys()
    if len(material_names)>0 and material_names[0].find("Material")!=0 and material_names[0][0]!="_": 
        model["materials"].append({
            "name": material_names[0],
            "transparent": get_bool_property(obj.material_slots[0].material, 'transparent'),
            "emission": get_bool_property(obj.material_slots[0].material, 'emission'),
        })

    fill_object_properties(model, obj)
    
    if string_starts_with(obj.name, 'attach_'):
        trans = get_godot_transform_of_obj(obj)
        model["attachments"].append({
            "type": get_property(obj, "attachment_type", "none"),
            "name": obj.name,
            "position": [obj.location[0], obj.location[2], -obj.location[1]],
            "transform": trans,
        })


for collection in scene.collection.children.values(): 
    collection.hide_render = True
#
for collection in scene.collection.children.values(): 
    unselect_all_objects()
    if collection.name.find("Collection")!=0 and collection.name[0] != "_":
        collection.hide_render = False
        model_name = collection.name
        is_ref = model_name[-4:] != "_phy"
        model_name = format_modelname(model_name)

        model = {"name": model_name, "res_path": "", "materials": [], "attachments":[], "properties": {
            "format":"obj", 
            "static":False, "rigid":False, "concave":False, "convex":False, 
            "two_sided":False, 
            "render_icon":False, "icon_size":64, "ortho_scale":1.6, "camera_look_at_z":1,
        }}

        for obj in collection.objects.values():
            scan_object_for_model(obj, model)
            
        model_filepath = output_folder / (model_name + "." + model["properties"]["format"])
        model["res_path"] = (resource_folder / (model_name+"."+model["properties"]["format"])).as_posix()
        print(model)
        
        if is_ref: 
            generate_mesh_resource(model)
            if model["properties"]["render_icon"]:
                render_icon(model)
        else:
            model["data"] = get_vertex_data(obj)
            generate_collision_shape_resource(model)
            if model["properties"]["static"]:
                generate_body_resource("static", model)
            if model["properties"]["rigid"]:
                generate_body_resource("rigid", model)
        
        export_selected_objects(model_filepath, model)

        for obj in collection.objects.values():
            obj.select_set(False)
        collection.hide_render = True


