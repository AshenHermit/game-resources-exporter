from ...resource_types import *

CFD = Path(__file__).parent.resolve()

print("")
print("[Source models exporting process]")
print("--  all collections in changed blend files will be exported to their own smd files stored next to the blend file.")
print("--  unlike smd files, qc files will be generated and saved only if they dont exist")
print("--  .mdl files are compiling with ")

class SourceBlenderModel(BlenderModel):
    @property
    def studiomdl_executable(self):
        return self.config.get("studiomdl_executable", "studiomdl.exe", True)

    @property
    def studiomdl_game_path(self):
        game_path = self.config.get("studiomdl_game_path", "C:\Program Files (x86)\Steam\steamapps\common\GarrysMod\garrysmod", True)
        if not Path(game_path).exists(): raise ExportConfig.PropertyException("studiomdl_game_path", "directory is missing")
        return game_path

    def export(self, **kwargs):
        # just to write it in config
        p = self.studiomdl_executable
        p = self.studiomdl_game_path

        blend_export_script = CFD/"blender_export/gm_blend_export.py"
        self.export_using_script(blend_export_script)