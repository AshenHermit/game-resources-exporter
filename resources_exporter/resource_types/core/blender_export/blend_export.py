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
    except:
        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        target = os.path.join(sys.prefix, 'lib', 'site-packages')
        print(python_exe)
        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "godot-parser", "-t", target])

        try:
            import godot_parser as gp
            importlib.reload(gp)
        except:
            print()
            print("####  WAIT A MINUTE  ####")
            print("The godot-parser module could not be installed in the Blender python.")
            print(f"This often happens due to the lack of write permissions to the folder: \n\"{target}\"")
            print("Try changing the permissions or run the exporter with administrator rights.")
install_requirements()

try:
    from . import gre_utils
    from . import exporter_core
    from . import game_resources
except:
    import gre_utils as gre_utils
    import exporter_core
    import game_resources

importlib.reload(gre_utils)
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

        # result = utils.apply_modifiers_of_all()
        # print(f"applying modifiers... {result}")
    
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
            gre_utils.unselect_all_objects()
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
    
def find_exporter_config():
    name = "exporter_config.json"
    filepath = Path(bpy.data.filepath).parent.resolve()
    for i in range(50): # wtf mb need to refactor this
        if not filepath.parent: return None
        filepath = filepath.parent
        for item in filepath.glob(name):
            return item.resolve()

def make_config_from_args():
    config_filepath = find_exporter_config()
    filepath = Path(bpy.data.filepath).resolve()

    config = Config()
    config.project_filepath = filepath
    config.external_config = {}
    if config_filepath.exists():
        config.external_config.update(json.loads(config_filepath.read_text()))
        config.game_root = config_filepath.parent / Path(config.external_config["game_root"]).resolve()
        config.raw_resources_folder = config_filepath.parent / Path(config.external_config["raw_folder"]).resolve()
        config.game_resources_dir = config_filepath.parent / Path(config.external_config["output_folder"]).resolve()

    return config

def export_project():
    """  setup and call export on `BlendExporter`"""
    config = make_config_from_args()

    exporter = BlendExporter(config)
    exporter.export_project()

if __name__ == '__main__':
    export_project()