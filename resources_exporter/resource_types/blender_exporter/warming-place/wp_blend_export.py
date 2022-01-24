import sys
from pathlib import Path

try:
    from ..blend_export import BlendGodotExporter

    from .. import utils
    from ..exporter_core import *
    from ..game_resources import *
except:
    sys.path.append(str(Path(__file__).parent.parent.resolve()))

    from blend_export import BlendGodotExporter
    import utils
    from exporter_core import *
    from game_resources import *

import sys
import argparse

class CustomViewModel(ViewModel):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

        self.anim_player_node_name = "AnimationPlayer"
        self.anim_installer_script = GodotResPath("src/utils/AnimWithEvents.cs")
        self.anim_installer_prop_name = "AnimationEvents"
    
    def make_godot_scene(self):
        saver = super().make_godot_scene()
        scene:gp.GDScene = saver.res

        if self.has_animation:
            anim_script_res = scene.add_ext_resource(str(self.anim_installer_script), "Script")
            anim_node_section = gp.GDNodeSection(self.anim_player_node_name, parent=".")
            anim_node_section.properties["script"] = anim_script_res.reference
            anim_node_section.properties[self.anim_installer_prop_name] = self.animation_events
            scene.add_section(anim_node_section)
        
        return saver

ModelResource.VIEW_MODEL_CLASS = CustomViewModel

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

    # config.object_processors.add(ObjectProcessor("processing.snow_maker"))

    exporter = BlendGodotExporter(config)
    exporter.export_project()

if __name__ == '__main__':
    main()