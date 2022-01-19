import sys
import os
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent.resolve()))
import importlib

# TODO:
sys.path.append("C:/users/user/appdata/roaming/python/python37/site-packages")

def install_requirements():
    try:
        import godot_parser as gp
    except ImportError:
        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        print(python_exe)
        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.call([python_exe, "-m", "pip", "install", "godot-parser"])

        import godot_parser as gp
        importlib.reload(gp)
install_requirements()

import utils
import exporter_core
import game_resources

importlib.reload(utils)
importlib.reload(exporter_core)
importlib.reload(game_resources)

from exporter_core import *
from game_resources import *

class BlendGodotExporter():
    def __init__(self, config:Config) -> None:
        self.config:Config = config

    def prepare_workspace_to_export(self):
        print("changing mode to OBJECT")
        bpy.ops.object.mode_set(mode = 'OBJECT')

        result = bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True, material=False, animation=False)
        print(f"getting rid of multi user data... {result}")

        result = utils.apply_modifiers_of_all()
        print(f"applying modifierss... {result}")
    
    def deactivate_everything(self):
        for collection in bpy.context.scene.collection.children.values(): 
            collection.hide_render = True

    def export_project(self):
        self.prepare_workspace_to_export()
        self.deactivate_everything()
        
        self.export_collections()

    def export_collections(self):
        for collection in bpy.context.scene.collection.children.values():
            utils.unselect_all_objects()
            collection.hide_render = False

            self.export_one_collection(collection)
            
            for obj in collection.objects.values():
                obj.select_set(False)
            collection.hide_render = True

    def export_one_collection(self, collection):
        model = ModelResource.from_collection(collection, self.config)
        if model is not None:
            model.export()
        return model

def main():
    raw_resources_folder:Path = Path(sys.argv[-3]).resolve()
    output_folder:Path = Path(sys.argv[-2]).resolve()
    game_root = Path(sys.argv[-1]).resolve()
    filepath = Path(bpy.data.filepath).resolve()

    config = Config()
    config.game_root = game_root
    config.game_resources_dir = output_folder
    config.raw_resources_folder = raw_resources_folder
    config.project_filepath = filepath

    config.object_processors.add(ObjectProcessor("blender_scripts.snow_maker"))

    exporter = BlendGodotExporter(config)
    exporter.export_project()

if __name__ == '__main__':
    main()