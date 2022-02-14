import typing
from ...resource_types import *
import re
import shlex
from .renderers.vmt_renderer import VMTRenderer

CFD = Path(__file__).parent.resolve()

class SourceTextResource(Resource):
    @property
    def is_using_goldsrc(self):
        return self.config.get("use_goldsrc", False, True)

    @property
    def text(self):
        if getattr(self, "_text", None) is None:
            self._text = self.filepath.read_text()
            if len(self._text)>0 and self._text[-1]!="\n": 
                self._text+="\n"
        return self._text
    @text.setter
    def text(self, value:str):
        self._text = value
    def write(self):
        self.filepath.write_text(self.text)
    def add_line_at_start(self, line_text:str):
        self.text = line_text+"\n"+self.text

class SourceBlenderModel(BlenderModel):
    @property
    def studiomdl_executable(self):
        return self.config.get("studiomdl_executable", "studiomdl.exe", True)

    @property
    def studiomdl_game_path(self):
        return self.config.game_root

    def export(self, **kwargs):
        # just to write it in config
        p = self.studiomdl_executable

        blend_export_script = CFD/"blender_export/src_blend_export.py"
        self.export_using_script(blend_export_script)

class SMDModel(SourceTextResource):
    def adjust_to_new_source(self):
        self.text = re.sub("\.bmp", "", self.text, flags=re.MULTILINE)
        self.write()

    def export(self, **kwargs):
        if not self.is_using_goldsrc:
            self.adjust_to_new_source()

    @staticmethod
    def get_extensions():
        return ["smd"]

class SourceQCModel(SourceTextResource):
    @property
    def studiomdl_executable(self):
        return self.config.get("studiomdl_executable", "studiomdl.exe", True)
    @property
    def blend_analog(self):
        return self.filepath.with_suffix(".blend")

    @property
    def cdmaterials(self):
        return self.filepath.parent.relative_to(self.config.raw_folder).as_posix()

    def matchall(self, pattern:str):
        return list(re.finditer(pattern, self.text, flags=re.MULTILINE))

    def get_cmd_args(self, cmd:str):
        matches:list[re.Match] = self.matchall("^\$"+cmd+" [^\n$]+$\n")
        if len(matches) == 0: return []
        return shlex.split(matches[0].group(0))[1:]
    def remove_cmd(self, cmd:str):
        self.text = re.sub("^\$"+cmd+" [^\n$]+$\n", "", self.text, flags=re.MULTILINE)
        self.text = re.sub("^\$"+cmd+"\s*$\n", "", self.text, flags=re.MULTILINE)
    def has_cmd(self, cmd:str):
        matches:list[re.Match] = self.matchall("^\$"+cmd+" [^\n$]+$\n")
        matches += self.matchall("^\$"+cmd+"\s*$\n")
        return len(matches) != 0
    
    @property
    def vmt_renderers(self) -> typing.Dict[str, VMTRenderer]:
        if getattr(self, "_vmt_renderers", None) is None:
            self._vmt_renderers = {}
        return self._vmt_renderers
    def get_vmt_renderer(self, material_name:str) -> VMTRenderer:
        if material_name not in self.vmt_renderers:
            renderer = VMTRenderer(self.filepath.parent/(material_name+".vmt"))
            renderer.basetexture = Path(self.cdmaterials)/material_name
            self.vmt_renderers[material_name] = renderer
        return self.vmt_renderers[material_name]

    def adjust_to_new_source(self):
        old_text = self.text
        self.text = re.sub("\.bmp", "", self.text, flags=re.MULTILINE)

        # set proper cdmaterials
        cmargs = self.get_cmd_args("cdmaterials")
        if len(cmargs)>0 and cmargs[0] == self.cdmaterials: pass
        else:
            self.remove_cmd("cdmaterials")
            self.add_line_at_start(f"$cdmaterials {self.cdmaterials}")

        self.remove_cmd("cd")
        self.remove_cmd("cdtexture")
        self.remove_cmd("cliptotextures")
        self.remove_cmd("flags")

        if self.has_cmd("texrendermode"):
            try:
                args = self.get_cmd_args("texrendermode")
                material_name = Path(args[0]).with_suffix("").name
                mode = args[1]
                if mode  == "additive":
                    self.get_vmt_renderer(material_name).additive = True
                if mode  == "masked":
                    print(colored(f'material "{material_name}" requires texture with alpha channel.', 'yellow'))
                    self.get_vmt_renderer(material_name).alphatest = True
                    bmp = self.get_vmt_renderer(material_name).filepath.with_suffix(".bmp").resolve()
                    psd = bmp.with_suffix(".psd").resolve()
                    if bmp.exists() and not psd.exists():
                        print(f'trying to convert "{bmp.name}" into psd...')
                        cmd = f"\"{self.config.image_magic_cmd}\" -colorspace RGB -transparent black  \"{bmp}\" \"{psd}\""
                        self.run_command(cmd)
            except: pass
        self.remove_cmd("texrendermode")

        for renderer in self.vmt_renderers.values():
            print(colored(f'saved material "{renderer.filepath.name}"', 'green'))
            renderer.write()
        
        self.write()
        if self.text != old_text:
            print(colored(f'changes made in file "{self.filepath.name}"', 'yellow'))

    def compile_model(self):
        cmd = f'"{self.studiomdl_executable}" -game "{self.config.game_root}" -nop4 -verbose "{self.filepath}"'
        self.run_command(cmd)
        
        # studiomdl after compiling writes files into root/models folder,
        # here we are moving them in wanted directory
        exported_dir = (self.config.game_root/"models")
        for file in exported_dir.glob(self.filepath.with_suffix("").name+".*"):
            utils.make_dirs_to_file(self.dst_filepath)
            shutil.copy(file, self.dst_filepath.parent/file.name)
            os.remove(file)

    def export(self, **kwargs):
        if not self.is_using_goldsrc:
            self.adjust_to_new_source()
        self.compile_model()

    @staticmethod
    def get_extensions():
        return ["qc"]

    @staticmethod
    def get_dependencies():
        return ["smd"]