from os import stat
import os
from pathlib import Path
import shlex
import sys
from typing import Generator
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import Storable, PathField
from serde import Model, fields
import shutil
import subprocess

CFD = Path(__file__).parent.resolve()

class ExportConfig(Storable):
    raw_folder: PathField
    output_folder: PathField
    output_root: PathField
    verbose: bool
    image_magic_cmd: fields.Str()

    def __init__(self, **kwargs) -> None:
        self.raw_folder:Path = Path("resources")
        self.output_folder:Path = Path("output")
        self.output_root:Path = Path("")
        self.verbose:bool = False
        self.image_magic_cmd:str = "convert"

        super().__init__(**kwargs)

    def normalize(self):
        self.raw_folder = self.raw_folder.resolve()
        self.output_folder = self.output_folder.resolve()
        self.output_root = self.output_root.resolve()

class ExportError(Exception):
    def __init__(self, filepath, message) -> None:
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)
    def __str__(self) -> str:
        return f"Failed to export a resource \"{self.filepath}\" : {self.message}"

class Resource:
    def __init__(self, filepath:Path, config:ExportConfig=None) -> None:
        self.filepath = filepath.resolve()
        self.config = config or ExportConfig()

    def __str__(self) -> str:
        short_path = self.filepath.relative_to(self.config.raw_folder).as_posix()
        return f"<{self.__class__.__name__:<16} \"{short_path}\">"

    def run_command(self, cmd):
        args = shlex.split(cmd)
        if self.config.verbose:
            print(cmd)
            with subprocess.Popen(args, shell=True) as proc:
                pass
        else:
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as proc:
                pass

    @property
    def dst_filepath(self):
        dst_filepath = self.filepath.relative_to(self.config.raw_folder)
        dst_filepath = self.config.output_folder / dst_filepath
        return dst_filepath

    def make_dirs_to_file(self, filepath:Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)

    def export(self, **kwargs):
        self.make_dirs_to_file(self.dst_filepath)
        shutil.copy(self.filepath, self.dst_filepath)

    @staticmethod
    def get_extensions():
        return []
