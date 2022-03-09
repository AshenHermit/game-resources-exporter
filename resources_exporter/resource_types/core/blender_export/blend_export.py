import sys
import os
import subprocess
from pathlib import Path

CFD = Path(__file__).parent.resolve()
sys.path.append(str(CFD.resolve()))
import importlib

# TODO:
# sys.path.append("C:/users/user/appdata/roaming/python/python37/site-packages")

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

try:
    from . import utils
    from . import exporter_core
    from . import game_resources
except:
    import utils
    import exporter_core
    import game_resources

importlib.reload(utils)
importlib.reload(exporter_core)
importlib.reload(game_resources)

try:
    from .exporter_core import *
    from .game_resources import *
except:
    from exporter_core import *
    from game_resources import *

class BlendExporter():
    def __init__(self, config:Config) -> None:
        self.config:Config = config

    def prepare_workspace_to_export(self):
        for collection in bpy.context.scene.collection.children.values():
            bpy.context.view_layer.layer_collection.children.get(collection.name).hide_viewport = False

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
        for collection_key in bpy.context.scene.collection.children.keys():
            def get_collection():
                return bpy.context.scene.collection.children.get(collection_key)
            collection = get_collection()
            utils.unselect_all_objects()
            collection = get_collection()
            collection.hide_viewport = False
            collection.hide_render = False
            collection.hide_select = False

            self.export_one_collection(collection)

            collection = get_collection()
            
            for obj in collection.objects.values():
                obj.select_set(False)
            collection.hide_viewport = True

    def export_one_collection(self, collection):
        model = ModelResource.from_collection(collection, self.config)
        if model is not None:
            model.export()
        return model

def make_config_from_args():
    raw_resources_folder:Path = Path(sys.argv[-4]).resolve()
    output_folder:Path = Path(sys.argv[-3]).resolve()
    game_root = Path(sys.argv[-2]).resolve()
    config_filepath = Path(sys.argv[-1]).resolve()
    filepath = Path(bpy.data.filepath).resolve()

    config = Config()
    config.game_root = game_root
    config.game_resources_dir = output_folder
    config.raw_resources_folder = raw_resources_folder
    config.project_filepath = filepath
    config.external_config = {}
    if config_filepath.exists():
        config.external_config.update(json.loads(config_filepath.read_text()))

    return config

def export_project():
    """  setup and call export on `BlendExporter`"""
    config = make_config_from_args()

    exporter = BlendExporter(config)
    exporter.export_project()

if __name__ == '__main__':
    export_project()