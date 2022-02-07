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
        blend_export_script = CFD/"blender_export/blend_export.py"
        self.export_using_script(blend_export_script)

    def export_using_script(self, blend_export_script:Path):
        raw_resources_folder = self.config.raw_folder
        export_folder = self.config.output_folder
        game_root = self.config.output_root
        cmd = f'blender "{self.filepath.as_posix()}" --background --python "{blend_export_script.as_posix()}"'
        str_args = [
            raw_resources_folder.as_posix(),
            export_folder.as_posix(),
            game_root.as_posix(),
            self.config._storage_file.resolve().as_posix(),
        ]
        cmd += " " + " ".join(map(lambda x: f'"{x}"', str_args))

        self.run_command(cmd)

    @staticmethod
    def get_extensions():
        return ["blend"]