import argparse
import pathlib
import pip
import godot_parser as gp
from multiprocessing import Condition
import traceback
import typing
import sys
import os
from math import *
from pathlib import Path
import shlex
import importlib


class ExportPlugin():
    def __init__(self, module_name:str="") -> None:
        self.module_name = module_name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(\"{self.module_name}\")"

    def __str__(self):
        return f"<{self.__class__.__name__} \"{self.module_name}\">"
        
    def execute(self, **kwargs):
        """module must have method `main` as entry point"""
        self.execute_method("main", **kwargs)

    def execute_method(self, method_name, **kwargs):
        try:
            module = importlib.import_module(self.module_name)
            print(f"executing {self!r}...")
            method = getattr(module, method_name, None)
            if method is not None:
                method(**kwargs)
            else:
                print(f"no method \"{method_name}\"")
        except:
            traceback.print_exc()

class ObjectProcessor(ExportPlugin):
    def __init__(self, module_name: str = "") -> None:
        super().__init__(module_name)
        
    def execute(self, obj=None, **kwargs):
        self.execute_method("process_obj", obj=obj, **kwargs)
    
class ExportPluginsLibrary():
    def __init__(self) -> None:
        self.__plugins:list[ExportPlugin] = []
    
    def add(self, plugin):
        self.__plugins.append(plugin)

    def execute_all(self, **kwargs):
        for plugin in self.__plugins:
            plugin.execute(**kwargs)

class Config:
    game_root:Path
    game_resources_dir:Path
    raw_resources_folder:Path
    project_filepath:Path

    object_processors: ExportPluginsLibrary = ExportPluginsLibrary()
