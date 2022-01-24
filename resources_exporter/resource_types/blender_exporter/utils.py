import argparse
import pathlib
import pip
from multiprocessing import Condition
import traceback
import typing
import bpy
import sys
import os
from math import *
from pathlib import Path
from mathutils import Vector
import shlex
import time

def format_modelname(model_name):
    if model_name[-4:] == "_ref": model_name = model_name[:-4]
    return model_name

def unselect_all_objects():
    for collection in bpy.context.scene.collection.children.values():
        for obj in collection.objects.values():
            obj.hide_set(False)
            obj.select_set(False)

def select_only_objects(objects=None):
    objects = objects or []
    for collection in bpy.context.scene.collection.children.values():
        for obj in collection.objects.values():
            obj.hide_set(False)
            obj.select_set(False)

    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)


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

def export_animation_events(obj):
    bpy.context.view_layer.objects.active = obj
    fps = bpy.context.scene.render.fps
    markers_by_actions = {}
    for action in bpy.data.actions:
        markers = []
        for marker in action.pose_markers:
            args = shlex.split(marker.name)
            markers.append({
                "event": args[0],
                "args": args[1:],
                "time": 1 / fps * marker.frame
            })
        markers_by_actions[action.name] = markers
    return markers_by_actions

def apply_modifiers_of_all():
    for obj in bpy.context.view_layer.objects:
        if obj.type=="MESH":   
            obj.select_set(state=True)
            bpy.context.view_layer.objects.active = obj
        else:
            obj.select_set(state=False)

    active = bpy.context.view_layer.objects.active
    if active is not None and active.type == 'MESH':
        bpy.ops.object.convert(target="MESH")
    return {'FINISHED'}