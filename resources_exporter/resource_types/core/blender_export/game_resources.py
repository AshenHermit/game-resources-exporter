import argparse
from email.policy import strict
from enum import Enum, auto
import json
import pathlib
import pip

from multiprocessing import Condition
import traceback
import typing
import bpy, bpy_types
import bpy.types
import sys
import os
from math import *
from pathlib import Path
import shlex

try:
    from . import utils
    from .exporter_core import *
except:
    import utils
    from exporter_core import *

class GodotResPath(type(pathlib.Path())):
    def __str__(self) -> str:
        f = getattr(self, "_flavour", argparse.Namespace(sep="\\"))
        return "res://"+super().__str__().replace(f.sep, '/')

    @property
    def pure_name(self):
        return self.with_suffix("").name

class GodotResSaver():
    def __init__(self, res:gp.GDFile, filepath:Path) -> None:
        self.res:gp.GDFile = res
        self.filepath:Path = filepath
    
    def save(self):
        self.res.write(str(self.filepath.resolve()))

class GDTypedResource(gp.GDResource):
    def __init__(self, type:str="Resource", *sections: gp.GDSection) -> None:
        super().__init__(*sections)
        self.get_sections()[0].header.attributes["type"] = type

class GameResource():
    def __init__(self, config:Config=None, name:str="") -> None:
        self.config:Config = config or Config()
        self.name = name

    def apply_properties(self, props:dict):
        for key in props.keys():
            value = getattr(self, key, None)
            if type(value) == bool:
                try:
                    setattr(self, key, 
                        int(props[key])==1)
                except: pass
            else:
                setattr(self, key, props[key])

    @property
    def output_path(self)->Path:
        """`<out_resources_dir> / <file_relative_to_raw_resources_dir> ` 
        ```text
        if
        filepath           = "./resources/keke/file.png"
        raw_resources      = "./resources/"
        game_resources_dir = "./project/assets/"
        then
        output_path        = "./project/assets/keke/file.png"
        ```
        """
        rel_filepath = self.config.project_filepath.with_name(self.name)
        rel_filepath = rel_filepath.relative_to(self.config.raw_resources_folder)
        output_path = self.config.game_resources_dir / rel_filepath
        return output_path

    @property
    def res_path(self)->GodotResPath:
        rel_path = GodotResPath(self.output_path.relative_to(self.config.game_root))
        return rel_path

    def export(self, **kwargs):
        pass

class MaterialResource(GameResource):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)
        self.tex_name = name
        self.type = "SpatialMaterial"
        self.emission = False
        self.two_sided = False

        self.material_data = None
    
    @staticmethod
    def from_material_data(material_data, config:Config=None):
        material = MaterialResource(config, material_data.name)
        material.material_data = material_data
        material.apply_properties(dict(material_data.items()))
        return material

    def get_textures(self):
        try:
            return [Path(x.image.filepath) for x in self.material_data.node_tree.nodes if x.type=='TEX_IMAGE']
        except:
            return []

    @property
    def output_path(self)->Path:
        return super().output_path.with_name(f"mat_{self.name}.tres")

    def format_tex_to_relpath(self, path, rel_to)->Path:
        path = Path(path)
        path = (Path("C:/") / rel_to) / Path(path.as_posix().replace("//..", ".."))
        path = path.with_name(path.name.replace(".psd", ".png"))
        path = path.resolve(strict=False).relative_to("C:/")
        return GodotResPath(path)

    def find_in_ntree(self, node_type):
        for node in self.material_data.node_tree.nodes:
            if node.type == node_type:
                return node
        return None
    @property
    def material_output(self):
        return self.find_in_ntree("OUTPUT_MATERIAL")

    def __iterate_inputs(self, start_node):
        for inp in  start_node.inputs:
            yield inp
            for link in inp.links:
                yield from self.__iterate_inputs(link.from_node)

    def iterate_inputs(self):
        yield from self.__iterate_inputs(self.material_output)

    def find_node(self, mro_of_node, name_of_output=None, name_of_inp_output_goes_into=None, mro_of_node_output_goes_into=None, execlude_mro_of_node_ogt:list=None):
        def string_matches(a,b):
            return b.strip().lower().find(a.strip().lower())!=-1

        for node in self.material_data.node_tree.nodes:
            if mro_of_node not in type(node).__mro__: continue

            if name_of_output is not None:
                output = None

                for out in node.outputs:
                    if string_matches(out.name, name_of_output):
                        output = out
                if output is None: continue

            if name_of_inp_output_goes_into is not None:
                if len(output.links)>0:
                    matches = False
                    for link in output.links:
                        if string_matches(link.to_socket.name, name_of_inp_output_goes_into):
                            matches = True
                    if not matches: continue

            if mro_of_node_output_goes_into is not None:
                if len(output.links)>0:
                    matches = False
                    for link in output.links:
                        mro = type(link.to_node).__mro__
                        if mro_of_node_output_goes_into in mro:
                            matches = True
                        # execludes
                        if execlude_mro_of_node_ogt is not None:
                            for exec_type in execlude_mro_of_node_ogt:
                                if exec_type in mro:
                                    matches = False
                    if not matches: continue

            return node

        return None

    @property
    def texture_res_path(self)->Path:
        """ returns the path to a png image associated with color input of shader in shader editor """
        tex_image_node = self.find_node(bpy.types.ShaderNodeTexImage, "color", "color", bpy_types.ShaderNode, [bpy.types.ShaderNodeNormalMap])
        if tex_image_node:
            if tex_image_node.image is not None:
                return self.format_tex_to_relpath(tex_image_node.image.filepath, self.res_path.parent)
        return None

    @property
    def emission_tex_res_path(self)->Path:
        """ returns the path to a png image associated with emission input of shader in shader editor """
        tex_image_node = self.find_node(bpy.types.ShaderNodeTexImage, "color", "emission", bpy_types.ShaderNode)
        if tex_image_node:
            if tex_image_node.image is not None:
                return self.format_tex_to_relpath(tex_image_node.image.filepath, self.res_path.parent)
        return None

    @property
    def normal_tex_res_path(self)->Path:
        """ returns the path to a png image associated with normal map node in shader editor """
        tex_image_node = self.find_node(bpy.types.ShaderNodeTexImage, "color", "color", bpy.types.ShaderNodeNormalMap)
        if tex_image_node:
            if tex_image_node.image is not None:
                return self.format_tex_to_relpath(tex_image_node.image.filepath, self.res_path.parent)
        return None

    @property
    def transparent(self):
        return self.material_data.blend_method != "OPAQUE"

    def export(self, **kwargs):
        if self.texture_res_path is not None:
            self.make_textured_res().save()
        else:
            self.export_colored_res().save()

    def make_textured_res(self):
        mat_res = GDTypedResource(self.type)

        tex_res = mat_res.add_ext_resource(str(self.texture_res_path), "Texture")
        mat_section = gp.GDResourceSection()
        if self.two_sided: mat_section.properties['params_cull_mode'] = 2
        if self.transparent:
            mat_section.properties['flags_transparent'] = True
            mat_section.properties["params_depth_draw_mode"] = 1
        mat_section.properties["albedo_texture"] = tex_res.reference
        
        if self.emission_tex_res_path is not None:
            emm_res = mat_res.add_ext_resource(str(self.emission_tex_res_path), "Texture")
            mat_section.properties["emission_enabled"] = True
            mat_section.properties["emission_texture"] = emm_res.reference

        if self.normal_tex_res_path is not None:
            nrm_res = mat_res.add_ext_resource(str(self.normal_tex_res_path), "Texture")
            mat_section.properties["normal_enabled"] = True
            mat_section.properties["normal_scale"] = 1.0
            mat_section.properties["normal_texture"] = nrm_res.reference
        
        mat_res.add_section(mat_section)
        return GodotResSaver(mat_res, self.output_path)

    def export_colored_res(self):
        mat_res = GDTypedResource(self.type)

        mat_section = gp.GDResourceSection()

        mat_res.add_section(mat_section)
        return GodotResSaver(mat_res, self.output_path)

class ModelResource(GameResource):
    VIEW_MODEL_CLASS:typing.Type
    PHYSICS_MODEL_CLASS:typing.Type

    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

        self.collection_name = "Collection"
        self.materials:dict[str, MaterialResource] = {}
        self.related_objects = []

    @property
    def collection(self):
        return bpy.context.scene.collection.children[self.collection_name]

    @property
    def phy_model_name(self):
        return self.name+"_phy"
    @property
    def ref_model_name(self):
        return self.name+"_ref"
    @property
    def has_phy_model(self)->Path:
        return bpy.context.scene.collection.children.find(self.phy_model_name) != -1
    @property
    def has_ref_model(self)->Path:
        collections = bpy.context.scene.collection.children
        return collections.find(self.ref_model_name) != -1 or collections.find(self.name) != -1

    def _process_object(self, obj):
        pass
    
    @staticmethod
    def from_collection(collection, config:Config=None):
        if collection.name.find("Collection")!=-1: return None
        if collection.name[0] == "_": return None
        if len(list(collection.objects.values()))==0: return None

        model_name:str = collection.name
        if model_name.endswith("_phy"):
            model_name = model_name[:model_name.rfind("_phy")]
            model:ModelResource = ModelResource.PHYSICS_MODEL_CLASS(config)
        else:
            pref_pos = model_name.rfind("_ref")
            if pref_pos!=-1: model_name = model_name[:pref_pos]
            model:ModelResource = ModelResource.VIEW_MODEL_CLASS(config)
        
        model.collection_name = collection.name
        model.name = model_name

        materials_data = []
        for obj in collection.objects.values():
            model.related_objects.append(obj)
            bpy.context.view_layer.objects.active = obj
            model._process_object(obj)
            model.apply_properties(obj)
            materials_data += list(map(lambda x: x.material, obj.material_slots.values()))
        
        for material_data in materials_data:
            material = MaterialResource.from_material_data(material_data, config)
            if material is not None:
                model.materials[material.material_data.name] = material

        return model
    
    def select_related_objects(self):
        utils.select_only_objects(list(self.collection.objects.values()))

    def export_obj(self):
        self.select_related_objects()
        filepath = self.output_path.with_suffix(".obj")
        bpy.ops.export_scene.obj(
            filepath=filepath.as_posix(),
            check_existing=False,
            use_selection=True,
            use_triangles=True,
            axis_forward='-Z',
            use_mesh_modifiers=True,
            axis_up='Y')

    def export_glb(self):
        self.select_related_objects()
        filepath = self.output_path.with_suffix(".glb")
        bpy.ops.export_scene.gltf(
            filepath=filepath.as_posix(),
            check_existing=False,
            use_selection=True,
            # export_materials="NONE",
            export_lights=True,
            )

class ViewModel(ModelResource):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

        self.animation_events = {}

        # properties
        self.format = "obj"

        self.render_icon = False
        self.icon_size = 64
        self.camera_look_at_z = 1.0
        self.ortho_scale = 1.0
        self.auto_pos_camera = True

    def _process_object(self, obj):
        self.config.object_processors.execute_all(obj=obj)
        self.animation_events.update(utils.export_animation_events(obj))

    def export(self, **kwargs):
        for material in self.materials.values():
            material.export(**kwargs)

        if self.format == "obj":
            self.export_obj()
        elif self.format == "glb":
            self.export_glb()

        if self.render_icon:
            self._render_icon()

        self.make_godot_scene().save()

    @property
    def output_path(self) -> Path:
        return super().output_path.with_suffix("."+self.format)
    @property
    def output_scene_path(self) -> Path:
        return super().output_path.with_suffix(".tscn")
    
    @property
    def mesh_res_path(self):
        return self.res_path.with_suffix("."+self.format)

    @property
    def is_mesh(self):
        return self.format == "obj"

    @property
    def has_animation(self):
        return self.format == "glb"
        
    def make_godot_scene(self):
        scene = gp.GDScene()

        if self.is_mesh: res_type = "ArrayMesh"
        else: res_type = "PackedScene"
        geometry_res = scene.add_ext_resource(str(self.mesh_res_path), res_type)

        if self.is_mesh:
            mesh_section = gp.GDNodeSection(self.name, type="MeshInstance")
            mesh_section.properties["mesh"] = geometry_res.reference

            for i, material in enumerate(self.materials.values()):
                mat_res = scene.add_ext_resource(str(material.res_path), "Material")
                mesh_section.properties[f"material/{i}"] = mat_res.reference
            
            scene.add_section(mesh_section)
        else:
            mesh_section = gp.GDNodeSection(self.name, instance=geometry_res.id)
            scene.add_section(mesh_section)

            for i, obj in enumerate(self.related_objects):
                obj_name = obj.name.replace(".", "")
                child_section = None

                if obj.type == "LIGHT":
                    if obj.data.type == "POINT":
                        child_section = gp.GDNodeSection(obj_name+"_Orientation", type=None, parent=obj_name, index=0)
                        child_section.properties[f"shadow_enabled"] = True
                        child_section.properties[f"omni_attenuation"] = 14.0
                        child_section.properties[f"omni_range"] = obj.data.cutoff_distance
                        energy_convert = 0.0041726618
                        child_section.properties[f"light_energy"] = obj.data.energy * energy_convert
                        
                else:
                    child_section = gp.GDNodeSection(obj_name, type=None, parent=".", index=i)
                    for m, mat_key in enumerate(obj.material_slots.keys()):
                        if mat_key in self.materials:
                            material = self.materials[mat_key]
                            mat_res = scene.add_ext_resource(str(material.res_path), "Material")
                            child_section.properties[f"material/{m}"] = mat_res.reference
                        
            
                if child_section is not None:
                    scene.add_section(child_section)

        return GodotResSaver(scene, self.output_scene_path)

    def _render_icon(self):
        self.select_related_objects()
        scene = bpy.context.scene
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 8
        scene.render.resolution_x = self.icon_size
        scene.render.resolution_y = self.icon_size
        if self.auto_pos_camera:
            scene.camera.data.type = "ORTHO"
            scene.camera.location[0] = 1
            scene.camera.location[1] = -1
            scene.camera.location[2] = 1 + self.camera_look_at_z
            scene.camera.data.ortho_scale = self.ortho_scale
            scene.camera.rotation_euler[0] = pi/4
            scene.camera.rotation_euler[1] = 0
            scene.camera.rotation_euler[2] = pi/4
        scene.render.film_transparent = True
        filepath = self.output_path.with_name(self.name+"_icon.png")
        scene.render.filepath = filepath.as_posix()
        bpy.ops.render.render(write_still=True)

ModelResource.VIEW_MODEL_CLASS = ViewModel

class PhysicsModel(ModelResource):
    class BodyType(Enum):
        RIGID = auto()
        STATIC = auto()
        KINEMATIC = auto()
    
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

        # properties
        self.static = False
        """ generate static body """
        self.rigid = False
        """ generate rigid body """
        self.kinematic = False
        """ generate rigid body """
        self.convex = False
        """ if True - use convex geometry, if False - use concave geometry. """

        self.margin = 0.04

        self.mesh_points = []
    
    def _process_object(self, obj):
        self.mesh_points += utils.get_vertex_data(obj)

    def export(self, **kwargs):
        self.make_collision_shape().save()
        if self.rigid:     self.make_body(self.BodyType.RIGID).save()
        if self.static:    self.make_body(self.BodyType.STATIC).save()
        if self.kinematic: self.make_body(self.BodyType.KINEMATIC).save()
    
    @property
    def collision_shape_path(self):
        return self.output_path.with_name(self.name+"_phy_collision_shape.tscn")
    @property
    def collision_shape_res_path(self):
        return self.res_path.with_name(self.collision_shape_path.name)
    @property
    def reference_model_res_path(self):
        return self.res_path.with_suffix(".tscn")
    
    @property
    def static_body_path(self):
        return self.output_path.with_name(self.name+"_static_body.tscn")
    @property
    def rigid_body_path(self):
        return self.output_path.with_name(self.name+"_rigid_body.tscn")
    @property
    def kinematic_body_path(self):
        return self.output_path.with_name(self.name+"_kinematic_body.tscn")

    def make_collision_shape(self):
        scene = gp.GDScene()
        data_res_type = "ConcavePolygonShape" if not self.convex else "ConvexPolygonShape"
        prop_name = "data" if not self.convex else "points"
        mesh_data_res = scene.add_sub_resource(data_res_type)
        mesh_data_res.properties[prop_name] = gp.GDObject("PoolVector3Array", *self.mesh_points)
        mesh_data_res.properties["margin"] = self.margin

        shape_section = gp.GDNodeSection(
            self.collision_shape_path.with_suffix("").name, 
            type="CollisionShape")
        shape_section.properties["shape"] = mesh_data_res.reference

        scene.add_section(shape_section)
        return GodotResSaver(scene, self.collision_shape_path)

    def make_body(self, body_type:BodyType):
        body_type_int = body_type.value-1
        
        paths = [self.rigid_body_path, self.static_body_path, self.kinematic_body_path]
        output_path = paths[body_type_int]

        scene = gp.GDScene()
        ref_model_res = scene.add_ext_resource(str(self.reference_model_res_path), "PackedScene")
        col_shape_res = scene.add_ext_resource(str(self.collision_shape_res_path), "PackedScene")

        type = ["RigidBody", "StaticBody", "KinematicBody"][body_type_int]

        with scene.use_tree() as tree:
            tree.root = gp.Node(output_path.with_suffix("").name, type=type)
            tree.root.add_child(
                gp.Node(
                    self.reference_model_res_path.pure_name,
                    instance=ref_model_res.id
                )
            )
            tree.root.add_child(
                gp.Node(
                    self.collision_shape_res_path.pure_name,
                    instance=col_shape_res.id
                )
            )
        
        return GodotResSaver(scene, output_path)

ModelResource.PHYSICS_MODEL_CLASS = PhysicsModel