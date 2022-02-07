from .. import utils
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
    class PropertyException(Exception):
        def __init__(self, key:str, message:str, *args) -> None:
            self.key = key
            self.message = message
            super().__init__(*args)
        def __str__(self) -> str:
            return f"invalid value of config property '{self.key}' : {self.message}"

    raw_folder: PathField = Path("resources")
    output_folder: PathField = Path("output")
    output_root: PathField = Path("")
    verbose: bool = False
    image_magic_cmd: fields.Str() = "convert"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
    def dst_filepath(self)->Path:
        dst_filepath = self.filepath.relative_to(self.config.raw_folder)
        dst_filepath = self.config.output_folder / dst_filepath
        return dst_filepath

    @property
    def pure_name(self)->str:
        return self.filepath.with_suffix("").name

    def export(self, **kwargs):
        utils.make_dirs_to_file(self.dst_filepath)
        shutil.copy(self.filepath, self.dst_filepath)

    @staticmethod
    def get_extensions():
        return []
