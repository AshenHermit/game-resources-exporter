from ...resource_types import *

CFD = Path(__file__).parent.resolve()

class GodotXRBlenderModel(BlenderModel):
    def export(self, **kwargs):
        blend_export_script = CFD/"blender_export/gxr_blend_export.py"
        self.export_using_script(blend_export_script)