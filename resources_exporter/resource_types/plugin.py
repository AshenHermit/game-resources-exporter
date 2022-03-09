from functools import cache
import typing
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
from .resource_base import Command, Resource

import importlib
import inspect

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class Plugin():
    CURRENT_LOADING_INSTANCE = None

    def __init__(self, id:str=None) -> None:
        self.id = id or ""
        self.name = utils.snake_case_to_title(self.id)
        self.resource_classes = []
        self.commands:list[Command] = []

    def load_scripts_in_dir(self, directory:Path):
        directory = Path(directory)
        for file in directory.glob("*.py"):
            self.load_script(file)
    
    def load_script(self, script_path:Path):
        script_path = Path(script_path)
        self.__class__.CURRENT_LOADING_INSTANCE = self
        
        module_path = script_path.relative_to(CFD.parent.parent)\
            .with_suffix("").as_posix().replace("/", ".")
        module = importlib.import_module(module_path)
        module = importlib.reload(module)

        for var in module.__dict__.values():
            if not inspect.isclass(var): continue
            if Resource not in inspect.getmro(var): continue
            self.add_resource(var)

    def add_resource(self, res_class):
        if res_class in self.resource_classes: return
        self.resource_classes.append(res_class)
        Resource._give_subclass(res_class)

    def add_command(self, cmd:Command):
        self.commands.append(cmd)

def plugin_cmd(name:str, description:str):
    def decorator(func):
        if Plugin.CURRENT_LOADING_INSTANCE is not None:
            cmd = Command(func, name, description)
            Plugin.CURRENT_LOADING_INSTANCE.add_command(cmd)
        def wrapper():
            return func()
        return wrapper
    return decorator

def set_plugin_name(name:str):
    if Plugin.CURRENT_LOADING_INSTANCE is not None:
        Plugin.CURRENT_LOADING_INSTANCE.name = name