import sys
from pathlib import Path
CFD = Path(__file__).parent.resolve()
sys.path.append(str(CFD.resolve()))
try:
    from ....resource_types.core.blender_export.blend_export import *
except:
    sys.path.append(str((CFD/"../../../resource_types/core/blender_export/").resolve()))
    from blend_export import *

class CustomPhysicsModel(PhysicsModel):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)
        # properties
        self.important_wife_property = "A VIEW MODEL"
    
    def export(self, **kwargs):
        print(f"IM COOL PHYSICS MODEL {self.name} AND MY WIFE IS {self.important_wife_property}. END OF TRANSMISSION.")
        return super().export(**kwargs)

ModelResource.PHYSICS_MODEL_CLASS = CustomPhysicsModel

if __name__ == '__main__':
    export_project()