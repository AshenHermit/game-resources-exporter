import sys
from pathlib import Path

CFD = Path(__file__).parent.resolve()
try:
    from ....resource_types.blender_export.blend_export import *
except:
    sys.path.append(str((CFD/"../../../resource_types/blender_export/").resolve()))
    from blend_export import *

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

def export_project():
    config = make_config_from_args()
    # config.object_processors.add(ObjectProcessor("processing.snow_maker"))

    exporter = BlendExporter(config)
    exporter.export_project()

if __name__ == '__main__':
    export_project()