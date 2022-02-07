import shutil
import sys
from pathlib import Path
import typing
import os

CFD = Path(__file__).parent.resolve()
try:
    from ....resource_types.blender_export.blend_export import *
except:
    sys.path.append(str((CFD/"../../../resource_types/blender_export/").resolve()))
    from blend_export import *

import sys
import argparse
import subprocess

class QCFileMaker():
    class CollisionModel():
        def __init__(self) -> None:
            self.mass = -1
            self.concave = False
            self.phy_smd = "model_phy.smd"
            self.surfaceprop = "plastic"
        
        def render(self):
            qc = ""
            qc += f'$surfaceprop "{self.surfaceprop}"\n'
            qc += f'$collisionmodel "{self.phy_smd}"\n'
            qc += '{\n'

            if self.mass == -1: qc += f'    $automass\n'
            else:               qc += f'    $mass {self.mass}\n'

            if self.concave: qc += f'    $concave\n'

            qc += '}\n'
            qc += '\n'
            return qc

    def __init__(self, filepath:Path=None) -> None:
        self.filepath: Path = filepath

        self.modelname = "model"
        self.cdmaterials = "models/id/model"
        self.body_name = "body"
        self.body_smd = "model_ref.smd"
        self.idle_sequence_smd = "model_ref.smd"

        self.collisionmodel:QCFileMaker.CollisionModel = None

    def render(self):
        qc = ""
        qc += f'$modelname "{self.modelname}"\n'
        qc += f'$cdmaterials "{self.cdmaterials}"\n'
        qc += f'$body {self.body_name} "{self.body_smd}"\n'
        qc += f'$sequence idle "{self.idle_sequence_smd}"\n'
        qc += '\n'
        if self.collisionmodel is not None:
            qc += self.collisionmodel.render()
        return qc

    def write(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(self.render())

class MDLCompiler():
    def __init__(self, studiomdl_exe:str, studiomdl_game_path:Path, mdl_filepath:Path, qc_filepath:Path) -> None:
        self.studiomdl_exe:str = studiomdl_exe
        self.studiomdl_game_path:Path = Path(studiomdl_game_path)
        self.filepath:Path = mdl_filepath
        self.qc_maker = QCFileMaker(qc_filepath)

    @property
    def export_dir(self):
        return self.filepath.parent

    def compile(self):
        # dont write qc if its already exists
        if not self.qc_maker.filepath.exists():
            self.qc_maker.write()
        
        cmd = f'"{self.studiomdl_exe}" -game "{self.studiomdl_game_path}" -nop4 -verbose "{self.qc_maker.filepath}"'
        with subprocess.Popen(cmd) as proc: proc.wait()
        
        exported_dir = (self.studiomdl_game_path/"models")
        for file in exported_dir.glob(self.filepath.with_suffix("").name+".*"):
            shutil.copy(file, self.export_dir/file.name)
            os.remove(file)

class GMModel(ModelResource):
    MDL_COMPILERS:typing.Dict[str, MDLCompiler] = {}

    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)
    
    def export(self, **kwargs):
        self.export_smd()
        self.tune_qc_maker()

    @property
    def studiomdl_executable(self):
        return self.config.external_config["studiomdl_executable"]
    @property
    def studiomdl_game_path(self):
        return self.config.external_config["studiomdl_game_path"]

    @property
    def mdl_compiler(self) -> MDLCompiler:
        if self.name not in GMModel.MDL_COMPILERS:
            mdl_compiler = MDLCompiler(
                self.studiomdl_executable, self.studiomdl_game_path, 
                self.output_mdl, self.qc_filepath)
            GMModel.MDL_COMPILERS[self.name] = mdl_compiler
        return GMModel.MDL_COMPILERS[self.name]

    @property
    def qc_maker(self) -> QCFileMaker:
        return self.mdl_compiler.qc_maker

    def export_smd(self):
        self.select_related_objects()
        bpy.context.scene.vs.export_path = "//"
        bpy.ops.export_scene.smd(collection=self.collection.name)

    @property
    def smd_filepath(self)->Path:
        """<blend_file_dir> / <collection_name>.smd"""
        return self.config.project_filepath.with_name(self.collection.name+".smd")

    @property
    def qc_filepath(self)->Path:
        """<blend_file_dir> / <model_name>.qc"""
        return self.config.project_filepath.with_name(self.name+".qc")

    @property
    def output_mdl(self)->Path:
        """<blend_file_dir> / <model_name>.qc"""
        return self.output_path.with_name(self.name+".mdl")

    @property
    def output_materials_rel_path(self)->Path:
        """self.output_path dir relative to "<game_root>/materials", materials folder of addon"""
        rel_path =  self.output_path.relative_to(self.config.game_root/"materials")
        return rel_path
    
    @property
    def cdmaterials(self)->Path:
        """ file directory relative to resources folder 
        ```
        filepath    = "./resources/models/keke/cool_model.blend"
        cdmaterials = "models/keke"
        ```"""
        dir =  self.config.project_filepath.relative_to(self.config.raw_resources_folder).parent
        return dir

    @property
    def output_models_rel_path(self)->Path:
        """self.output_path dir relative to "<game_root>/models", models folder of addon"""
        rel_path =  self.output_mdl.relative_to(self.config.game_root/"models")
        return rel_path

    def tune_qc_maker(self):
        pass

class GMViewModel(GMModel):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

    def tune_qc_maker(self):
        self.qc_maker.modelname = self.name
        self.qc_maker.cdmaterials = self.cdmaterials
        self.qc_maker.body_name = self.name
        self.qc_maker.body_smd = self.smd_filepath.name
        self.qc_maker.idle_sequence_smd = self.smd_filepath.name

class GMPhysicsModel(GMModel):
    def __init__(self, config: Config = None, name: str = "") -> None:
        super().__init__(config, name)

        # properties
        self.mass = -1
        self.concave = False
        self.surfaceprop = "plastic"

    def tune_qc_maker(self):
        cm = QCFileMaker.CollisionModel()
        cm.surfaceprop = self.surfaceprop
        cm.mass = self.mass
        cm.concave = self.concave
        cm.phy_smd = self.smd_filepath.name
        self.qc_maker.collisionmodel = cm
    
ModelResource.VIEW_MODEL_CLASS = GMViewModel
ModelResource.PHYSICS_MODEL_CLASS = GMPhysicsModel

if __name__ == '__main__':
    export_project()

    for mdl_compiler in GMModel.MDL_COMPILERS.values():
        mdl_compiler.compile()