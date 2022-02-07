from ...resource_types import *

CFD = Path(__file__).parent.resolve()

class WPBlenderModel(BlenderModel):
    def export(self, **kwargs):
        blend_export_script = CFD/"blender_export/wp_blend_export.py"
        self.export_using_script(blend_export_script)

    @staticmethod
    def get_extensions():
        return ["blend"]