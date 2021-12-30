import argparse
from pathlib import Path
import glob
import shutil
import json
import platform
import os
from types import FunctionType
import traceback

CWD:Path = (Path(__file__) / "..").resolve()

class CmdArgs:
    def __init__(self, action, raw_folder, file, output_folder, game_root, verbose, image_magick_cmd="convert") -> None:
        self.action:str = action
        self.raw_folder:Path = raw_folder
        self.file:Path = file
        self.output_folder:Path = output_folder
        self.game_root:Path = game_root
        self.verbose:bool = verbose
        self.image_magick_cmd = image_magick_cmd

    @staticmethod
    def resolved_path(path_string):
        return Path(path_string).resolve()
    
    @staticmethod
    def parse_args(actions_list):
        parser = argparse.ArgumentParser()
        parser.add_argument('action', help="can be: "+actions_list)
        parser.add_argument('-i', '--raw-folder', type=CmdArgs.resolved_path)
        parser.add_argument('-f', '--file', type=CmdArgs.resolved_path)
        parser.add_argument('-o', '--output-folder', type=CmdArgs.resolved_path)
        parser.add_argument('-g', '--game-root', type=CmdArgs.resolved_path)
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        parser.add_argument('--image-magick-cmd', type=str, default="convert")
        args = parser.parse_args()
        c_args = CmdArgs(**vars(args))
        return c_args

class ResourcesExporter:
    def __init__(self, verbose_output:bool=False, game_root:Path=None, image_magick_cmd="convert") -> None:
        self.file = ""
        self.image_magick_cmd = image_magick_cmd
        self.file_registry_path = CWD / "file_registry.json"
        self.file_registry:dict = {}
        self.load_file_registry()
        
        self.verbose_output:bool = verbose_output
        self.game_root:Path = game_root

    def load_file_registry(self):
        if not self.file_registry_path.exists():
            return {}

        file_registry = {}
        text = self.file_registry_path.read_text(encoding='utf-8')
        if text != "":
            file_registry = json.loads(text)
        else:
            file_registry = {}
        self.file_registry = file_registry

    def save_file_registry(self):
        json_text = json.dumps(self.file_registry, indent=2)
        self.file_registry_path.write_text(json_text, encoding='utf-8')

    def make_dirs(self, path:Path):
        while path.as_posix().find(".")!=-1:
            path = (path / "..").resolve()
            
        Path(path).mkdir(parents=True, exist_ok=True)

    def is_file_changed(self, file:Path):
        filepath:str = file.as_posix()
        stat = file.stat()
        if filepath in self.file_registry:
            if stat.st_mtime > self.file_registry[filepath]["mtime"]:
                self.file_registry[filepath]["mtime"] = stat.st_mtime
                return True
        else:
            self.file_registry[filepath] = {"mtime": stat.st_mtime}
            return True
        return False

    def run_command(self, cmd):
        is_on_windows = platform.system() == "Windows"
        if not self.verbose_output and not is_on_windows:
            cmd += " > /dev/null"
        os.system(cmd)

    def copy_file(self, source, destination):
        fileA = open(source, 'rb')
        fileB = open(destination, 'wb')
        shutil.copyfileobj(fileA, fileB)

    def is_file_execluding(self, filepath:Path, extension:str, execlude_ends_with:list[str]):
        filepath:str = str(filepath)
        for ending in execlude_ends_with: 
            if filepath.endswith(ending+"."+extension):
                return True
        return False

    def scan_changed_files_in_dir(self, root_dir:Path, extension:str, execlude_ends_with:list[str]=[]):
        files:set[Path] = set()
        for filepath in glob.glob(root_dir.as_posix()+"/**/*."+extension, recursive=True):
            filepath:Path = Path(filepath).resolve()
            if self.is_file_changed(filepath):
                if not self.is_file_execluding(filepath, extension, execlude_ends_with): 
                    files.add(filepath)
        return files

    def transpose_filepath(self, filepath:Path, origin_root:Path, new_root:Path):
        path = new_root / Path(filepath.as_posix()[len(origin_root.as_posix())+1:])
        return path

    # custom_export_function(filepath, root_dir, output_folder)
    def export_file(self, root_dir:Path, output_folder:Path, extension:str, 
                    execlude_ends_with:list[str]=[], file_description="file", custom_export_function:FunctionType=None):
        files = self.scan_changed_files_in_dir(root_dir, extension, execlude_ends_with)

        for filepath in files:
            export_path = self.transpose_filepath(filepath, root_dir, output_folder)
            self.make_dirs(export_path)
            if custom_export_function is None:
                print(f"Copying {extension} {file_description}: {filepath}")
                self.copy_file(filepath, export_path)
            else:
                print(f"Exporting {extension} {file_description}: {filepath}")
                custom_export_function(filepath, root_dir, output_folder)

    def export_blend(self, blend_filepath:Path, export_folder:Path):
        model_name = blend_filepath.name[blend_filepath.name.rfind(".")]
        print(model_name)
        cmd = f'blender "{blend_filepath.as_posix()}" --background --python "{CWD.as_posix()}/blend_export.py" "{export_folder.as_posix()}" "{self.game_root.as_posix()}"'
        self.run_command(cmd)

    def convert_psd_to_png(self, filepath, root_dir, output_folder):
        export_path = self.transpose_filepath(filepath, root_dir, output_folder)
        export_path = export_path.with_name(export_path.name.replace(".psd", ".png"))
        cmd = f'{self.image_magick_cmd} "{filepath}[0]" "{export_path}"'
        self.run_command(cmd)

    def export_model(self, filepath:Path, root_dir:Path, output_folder:Path):
        export_path = self.transpose_filepath(filepath, root_dir, output_folder)
        export_folder = (export_path/'..').resolve()
        self.make_dirs(export_folder)
        print("Exporting blend project: "+filepath.as_posix())
        self.export_blend(filepath, export_folder)

    def export_sounds(self, root_dir:Path, output_folder:Path):
        self.export_file(root_dir, output_folder, "wav", [], "sound")
        self.export_file(root_dir, output_folder, "mp3", [], "sound")
        self.export_file(root_dir, output_folder, "ogg", [], "sound")

    def export_models(self, root_dir:Path, output_folder:Path):
        for filepath in glob.glob(root_dir.as_posix()+"/**/*.blend", recursive=True):
            filepath:Path = Path(filepath)
            if self.is_file_changed(filepath):
                self.export_model(filepath, root_dir, output_folder)

    def export_textures(self, root_dir:Path, output_folder:Path):
        self.export_file(root_dir, output_folder, "png", ["_uv"], "image")
        self.export_file(root_dir, output_folder, "ico", [], "image")
        self.export_file(root_dir, output_folder, "psd", [], "image", self.convert_psd_to_png)
        
class ExporterCLI:
    def __init__(self) -> None:
        self.actions = {
            "export_all": self.export_all,
            "export_textures": self.export_textures,
            "export_sounds": self.export_sounds,
            "export_models": self.export_models,
            "export_one_model": self.export_one_model,
        }

        self.exporter:ResourcesExporter = None

    def export_models(self):
        self.exporter.export_models(
            self.args.raw_folder, self.args.output_folder)

    def export_textures(self):
        self.exporter.export_textures(
            self.args.raw_folder, self.args.output_folder)
    
    def export_sounds(self):
        self.exporter.export_sounds(
            self.args.raw_folder, self.args.output_folder)

    def export_all(self):
        self.export_textures()
        self.export_models()
        self.export_sounds()
    
    def export_one_model(self):
        self.exporter.export_model(
            self.args.file,
            self.args.raw_folder, self.args.output_folder)
    
    def parse_args(self)->CmdArgs:
        actions_list = ", ".join(self.actions.keys())
        args:CmdArgs = CmdArgs.parse_args(actions_list)
        return args

    def run(self):
        self.args:CmdArgs = self.parse_args()
        self.exporter = ResourcesExporter(
            verbose_output = self.args.verbose, 
            game_root = self.args.game_root,
            image_magick_cmd = self.args.image_magick_cmd)

        action = self.args.action
        if action in self.actions:
            try:
                self.actions[action]()
            except:
                traceback.print_exc(1, chain=False)

        self.exporter.save_file_registry()

def main():
    # cli = ExporterCLI()
    # cli.run()
    pass

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class ResourcesExporterCLI:
    def __init__(self) -> None:
        pass

    def run(self):
        pass


def test_args():
    argparse.ArgumentParser()

if __name__ == '__main__':

    
    main()