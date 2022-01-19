import os
from pathlib import Path
from resources_exporter.resource_types.resource_base import ExportConfig, Resource

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class ModelResource(Resource):
    def export(self, **kwargs):
        return super().export(**kwargs)

    @staticmethod
    def get_extensions():
        return ["obj", "fbx"]


class BlenderModel(ModelResource):
    def export(self, **kwargs):
        model_name = self.filepath.with_suffix("").name
        raw_resources_folder = self.config.raw_folder
        export_folder = self.config.output_folder
        game_root = self.config.output_root
        cmd = f'blender "{self.filepath.as_posix()}" --background --python "{CFD.as_posix()}/blender_exporter/blend_export.py" "{raw_resources_folder.as_posix()}" "{export_folder.as_posix()}" "{game_root.as_posix()}"'
        self.run_command(cmd)

    @staticmethod
    def get_extensions():
        return ["blend"]