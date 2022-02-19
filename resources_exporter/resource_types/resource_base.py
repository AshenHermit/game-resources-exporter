from functools import cache
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
from termcolor import colored

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
    game_root: PathField = Path("")
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
    _subclasses = set()

    def __init__(self, filepath:Path, config:ExportConfig=None) -> None:
        self.filepath = filepath.resolve()
        self.config = config or ExportConfig()

    @staticmethod
    def _give_subclass(subcls):
        Resource._subclasses.add(subcls)

    @staticmethod
    def _get_max_name_length():
        length = max(map(lambda x: len(x.__name__)+2, Resource._subclasses))
        return length

    def __str__(self) -> str:
        short_path = self.filepath.relative_to(self.config.raw_folder).as_posix()
        name = self.__class__.__name__
        name += " "*int(max(self._get_max_name_length()-len(name), 0))
        return f"<{name} \"{short_path}\">"

    def run_command(self, cmd):
        args = shlex.split(cmd)
        if self.config.verbose:
            print(cmd)
            subprocess.STDOUT = sys.stdout
            process = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
            for c in iter(lambda: process.stdout.read(1), b''): 
                sys.stdout.write(c.decode('utf-8'))
        else:
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as proc:
                pass

    @property
    def dst_filepath(self)->Path:
        """`<out_resources_dir> / <file_relative_to_raw_resources_dir> ` 
        ```t
        if
        filepath           = "./resources/keke/file.png"
        raw_resources      = "./resources/"
        game_resources_dir = "./project/assets/"
        then
        output_path        = "./project/assets/keke/file.png"
        ```
        """
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

    @staticmethod
    def get_dependencies():
        return []
