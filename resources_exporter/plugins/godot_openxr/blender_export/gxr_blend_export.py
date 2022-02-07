import sys
from pathlib import Path

from numpy import save


CFD = Path(__file__).parent.resolve()
try:
    from ....resource_types.blender_export.blend_export import *
except:
    sys.path.append(str((CFD/"../../../resource_types/blender_export/").resolve()))
    from blend_export import *

import sys
import argparse

class CustomPhysicsModel(PhysicsModel):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)
        # properties
        self.pickable = False
        self.picked_up_layer = 0

        self.margin = 0.001

        self.pickable_script = GodotResPath("addons/godot-xr-tools/objects/Object_pickable.gd")
    
    def make_body(self, body_type: PhysicsModel.BodyType):
        saver = super().make_body(body_type)
        scene:gp.GDScene = saver.res
        if body_type == PhysicsModel.BodyType.RIGID:
            if self.pickable:
                pickable_script_res = scene.add_ext_resource(str(self.pickable_script), "Script")
                root_body = scene.get_node(".")
                root_body.properties["script"] = pickable_script_res.reference
                root_body.properties["highlight_mesh_instance"] = gp.objects.NodePath(self.name)
                root_body.properties["picked_up_layer"] = self.picked_up_layer
                scene.add_section(gp.sections.GDNodeSection("PickupCenter", type="Spatial", parent="."))
        return saver

ModelResource.PHYSICS_MODEL_CLASS = CustomPhysicsModel

if __name__ == '__main__':
    export_project()