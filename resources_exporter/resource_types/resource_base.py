from functools import cache
import codecs
import inspect
from io import StringIO
from tokenize import String
import typing
from .. import utils
from os import stat
import os
from pathlib import Path
import shlex
import sys
from typing import Callable, Generator
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import Storable, PathField
from serde import Model, fields
import shutil
import subprocess
from termcolor import colored
import locale

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
    image_magic_cmd: fields.Str() = "magick"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class ExportError(Exception):
    def __init__(self, filepath, message) -> None:
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)
    def __str__(self) -> str:
        return f"Failed to export a resource \"{self.filepath}\" : {self.message}"

class Command():
    def __init__(self, func:Callable, name:str=None, description:str=None, enabled=True) -> None:
        self.func:Callable = func
        self.name:str = name or utils.snake_case_to_title(func.__name__)
        self.description:str = description or self.name
        self.enabled = enabled

    @property
    def id(self):
        return self.func.__name__

class SettingSignature():
    def __init__(self, id:str, name:str=None, description:str=None, enabled=True) -> None:
        self.id:str = id
        self.name:str = name or utils.snake_case_to_title(id.__name__)
        self.description:str = description or self.name
        self.enabled = enabled

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

    def run_program(self, cmd):
        args = shlex.split(cmd)
        # args = ["chcp", "65001", "&"] + args

        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True) as process:
            out = process.stdout.read()
            err = process.stderr.read()
            if self.config.verbose:
                print(out)
                print(colored(err, 'red'))
                # for c in iter(lambda: process.stdout.read(1), b''):
                #     sys.stdout.write(c.decode('utf-8'))
            if err: raise Exception(err)
        return out

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

    @classmethod
    def get_commands(cls) -> typing.List[Command]:
        command_funcs = inspect.getmembers(cls, predicate=
            lambda x: getattr(x, "command", None) is not None)
        commands = list(map(lambda x: x[1].command, command_funcs))
        return commands
    
    @classmethod
    def get_settings_map(cls):
        key = cls.__qualname__ + "_settings"
        if not hasattr(cls, key):
            setattr(cls, key, {})
        return getattr(cls, key)
    
    @classmethod
    def get_settings(cls) -> typing.List[SettingSignature]:
        settings = []
        for ccls in inspect.getmro(cls)[:-1]:
            settings += ccls.get_settings_map().values()
        return settings

    @staticmethod
    def get_commands_of_classes(*classes) -> typing.List[Command]:
        commands = {}

        for cls in classes:
            new_cmds = cls.get_commands()
            if len(commands)==0:
                for cmd in new_cmds:
                    commands[cmd.id] = cmd
            else:
                new_ids = list(map(lambda x: x.id, new_cmds))
                cur_cmds = list(commands.values())
                for cmd in cur_cmds:
                    if cmd.id not in new_ids:
                        commands.pop(cmd.id)
        return list(commands.values())

    @staticmethod
    def get_settings_of_classes(*classes) -> typing.List[SettingSignature]:
        settings = {}
        for cls in classes:
            new_settings = cls.get_settings()
            if len(settings)==0:
                for setting in new_settings:
                    settings[setting.id] = setting
            else:
                new_ids = list(map(lambda x: x.id, new_settings))
                cur_settings = list(settings.values())
                for setting in cur_settings:
                    if setting.id not in new_ids:
                        settings.pop(setting.id)
        return list(settings.values())
        
    @staticmethod
    def get_icon() -> Path:
        return None

    @classmethod
    def add_setting(cls, id:str, name:str=None, description:str=None, enabled=True):
        setting = SettingSignature(id, name, description, enabled)
        cls.get_settings_map()[id] = setting

Resource.add_setting("observer_ignore", "Ignore by Observer", "File will be ignored by observer")

def res_cmd(name:str=None, description:str=None, enabled=True):
    def decorator(func:Callable):
        cmd = Command(func, name, description, enabled)

        def wrapper(res_instance):
            return func(res_instance)

        if enabled:
            wrapper.command = cmd
        return wrapper
    return decorator