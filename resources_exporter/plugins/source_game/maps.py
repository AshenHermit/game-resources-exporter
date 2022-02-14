from email.mime import base
from ...resource_types import *

class SourceMapResource(Resource):
    @property
    def vbsp_executable(self):
        return self.config.get("vbsp_executable", "vbsp.exe", True)

    @property
    def vvis_executable(self):
        return self.config.get("vvis_executable", "vvis.exe", True)

    @property
    def vrad_executable(self):
        return self.config.get("vrad_executable", "vrad.exe", True)
    
    @property
    def generated_bsp_filepath(self):
        return self.filepath.with_suffix(".bsp")

    @property
    def dst_bsp_filepath(self):
        return self.dst_filepath.with_suffix(".bsp")

    def compile_map(self):
        gen_args = f"-game \"{self.config.game_root}\" \"{self.filepath}\""

        self.run_command(f"\"{self.vbsp_executable}\" {gen_args}")
        self.run_command(f"\"{self.vvis_executable}\" {gen_args}")
        self.run_command(f"\"{self.vrad_executable}\" -StaticPropLighting -StaticPropPolys -both {gen_args}")

        if not self.generated_bsp_filepath.exists():
            raise Exception("Failed to generate bsp file")
            return

        if self.dst_bsp_filepath.exists(): os.remove(self.dst_bsp_filepath)
        shutil.copyfile(self.generated_bsp_filepath, self.dst_bsp_filepath)
        os.remove(self.generated_bsp_filepath)

    def export(self, **kwargs):
        self.compile_map()

    @staticmethod
    def get_extensions():
        return ["vmf"]