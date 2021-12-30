from pathlib import Path

class ResourcesGenerator():
    def __init__(self, game_root):
        self.game_root:Path = Path(game_root)
        self.res_text = ""
        self.message = ""
        self.ext_res_id = 1
        self.sub_res_id = 1

        self.attachment_types = {
            "none": 0,
            "spawn_point": 1,
        }

    def get_res_paths(self, object_data, extension="tscn"):
        res_folder = object_data["res_path"][:object_data["res_path"].rfind("/")]
        filepath = (self.game_root / (res_folder+"/"+object_data["name"]+"."+extension)).as_posix()
        return filepath, res_folder

    def begin_scene(self):
        self.res_text = ""
        self.ext_res_id = 1
        self.sub_res_id = 1
        self.add_line('[gd_scene format=2]')

    def add_line(self, line="", add_ext_res=False, add_sub_res=False):
        self.res_text += line + "\n"
        if add_ext_res: self.ext_res_id += 1
        if add_sub_res: self.sub_res_id += 1

    def get_resource_text(self):
        return self.res_text

    def print_status(self, status_text):
        self.message = status_text

    def get_attachment_type(self, string_type):
        if string_type in self.attachment_types:
            return self.attachment_types[string_type]
        else:
            return 0


    def save_scene(self, object_data):
        filepath, res_folder = self.get_res_paths(object_data, "tscn")
        if not Path(filepath).is_file() or True:
            if self.message!="": print(self.message)
            tscn = self.get_resource_text()
            with open(filepath, "w") as file:
                file.write(tscn)

    def list_to_sequence(self, l):
        return ",".join(map(str, l))

    def list_to_string_vector(self, l):
        return f'Vector3({self.list_to_sequence(l)})'

    def generate_mesh(self, object_data):
        filepath, res_folder = self.get_res_paths(object_data, "tscn")
        self.print_status("Generated mesh : "+object_data["name"])

        attachment_script_res_id = 0

        self.begin_scene()

        if object_data["properties"]["format"] == "obj":
            self.add_line(f'[ext_resource path="res://{object_data["res_path"]}" type="ArrayMesh" id={self.ext_res_id}]', add_ext_res=True)
        else:
            self.add_line(f'[ext_resource path="res://{object_data["res_path"]}" type="PackedScene" id={self.ext_res_id}]', add_ext_res=True)
        
        for i, material in enumerate(object_data["materials"]):
            self.add_line(f'[ext_resource path="res://{res_folder}/{material["name"]}.png" type="Texture" id={self.ext_res_id}]', add_ext_res=True)
            if material["emission"]: self.add_line(f'[ext_resource path="res://{res_folder}/{material["name"]}_emission.png" type="Texture" id={self.ext_res_id}]', add_ext_res=True)
        if len(object_data["attachments"])>0:
            attachment_script_res_id = self.ext_res_id
            self.add_line(f'[ext_resource path="res://scripts/attachment.gd" type="Script" id={self.ext_res_id}]', add_ext_res=True)

        self.add_line()
        
        for i, material in enumerate(object_data["materials"]):
            self.add_line(f'[sub_resource type="SpatialMaterial" id={self.sub_res_id}]', add_sub_res=True)
            if object_data["properties"]["two_sided"]: self.add_line(f'params_cull_mode = 2')
            if material["transparent"]: self.add_line(f'flags_transparent = true')
            stride = 1
            if material["emission"]:
                stride+=1
            self.add_line(f'albedo_texture = ExtResource( {2+i*stride} )')
            if material["emission"]: 
                self.add_line(f'emission_enabled = true')
                self.add_line(f'emission_texture = ExtResource( {2+i*stride+1} )')

        self.add_line()

        if object_data["properties"]["format"] == "obj":
            self.add_line(f'[node name="{object_data["name"]}" type="MeshInstance"]')
            self.add_line(f'mesh = ExtResource( 1 )')
        else:
            self.add_line(f'[node name="{object_data["name"]}" instance=ExtResource( 1 )]')
        
        for i, material in enumerate(object_data["materials"]):
            self.add_line(f'material/{i} = SubResource( {1+i} )')

        for attach in object_data["attachments"]:
            self.add_line()
            self.add_line(f'[node name="{attach["name"]}" type="Spatial" parent="."]')
            self.add_line(f'transform = Transform({self.list_to_sequence(attach["transform"])})')
            self.add_line(f'script = ExtResource( {attachment_script_res_id} )')
            self.add_line(f'attachment_type = {self.get_attachment_type(attach["type"])}')
        
        self.save_scene(object_data)


    def generate_collision_shape(self, object_data):
        object_data["name"] += "_collision_shape"
        filepath, res_folder = self.get_res_paths(object_data, "tscn")
        self.print_status("Generating collision shape : "+object_data["name"])
        self.begin_scene()

        type = "ConcavePolygonShape" if not object_data["properties"]["convex"] else "ConvexPolygonShape"
        data_name = "data" if not object_data["properties"]["convex"] else "points"
        # type = "ConcavePolygonShape"
        self.add_line(f'[sub_resource type="{type}" id=1]')
        data = str(object_data["data"])[1:-1]
        self.add_line(f'{data_name} = PoolVector3Array({data})')

        self.add_line(f'[node name="{object_data["name"]}" type="CollisionShape"]')
        self.add_line(f'shape = SubResource( 1 )')
        
        self.save_scene(object_data)

    def generate_body(self, type, object_data):
        object_data["name"] = object_data["name"][:-4]
        model_name = object_data["name"]
        object_data["name"] += "_"+type+"_body"
        filepath, res_folder = self.get_res_paths(object_data, "tscn")
        self.print_status("Generating "+type+" body : "+object_data["name"])

        self.begin_scene()

        self.add_line(f'[ext_resource path="res://{res_folder}/{model_name}.tscn" type="PackedScene" id=1]')
        self.add_line(f'[ext_resource path="res://{res_folder}/{model_name}_phy_collision_shape.tscn" type="PackedScene" id=2]')
        type = "RigidBody" if type=="rigid" else "StaticBody"
        self.add_line(f'[node name="{object_data["name"]}" type="{type}"]')
        self.add_line(f'[node name="{model_name}" parent="." instance=ExtResource( 1 )]')
        self.add_line(f'[node name="{model_name}_phy_collision_shape" parent="." instance=ExtResource( 2 )]')
        
        self.save_scene(object_data)
