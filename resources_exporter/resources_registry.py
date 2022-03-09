import argparse
from re import sub
import subprocess
from functools import cache, reduce
import os
from pathlib import Path
import shutil
from threading import Lock, RLock
import time
import traceback
from typing import Type
import typing
from termcolor import colored

from .resource_types.plugin import Plugin

from .storable import PathField, Storable
from .resource_types.resource_base import ExportConfig, Resource
from . import utils
from serde import Model, fields
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .file_system import *

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

PLUGINS_DIR = CFD/"plugins"

class ResourcesRegistry:
    """
    provides and stores resources classes
    """
    def __init__(self) -> None:
        self.resource_classes = set()
        self.res_classes_ext_map = {}
        self.plugins:list[Plugin] = []

    def register_plugin_in_dir(self, plugin_dir:Path):
        try:
            plugin = Plugin(plugin_dir.name)
            plugin.load_scripts_in_dir(plugin_dir)
            self.add_plugin(plugin)
        except:
            traceback.print_exc()
            plugin_path = plugin_dir.relative_to(CFD).as_posix()
            print(f"Failed to import plugin \"{plugin_path}\"")
    
    def register_core_plugin(self):
        plugin_dir = CFD/"resource_types/core"
        self.register_plugin_in_dir(plugin_dir)

    def register_plugin(self, plugin_id:str):
        plugins_dir = PLUGINS_DIR
        plugin_dir = plugins_dir/plugin_id
        self.register_plugin_in_dir(plugin_dir)

    @cache
    def _get_sorted_extensions(self, cache_key):
        """sorted depending on resources dependencies"""
        exts = list(self.res_classes_ext_map.keys())
        i = 0
        total_iter = 0
        while i<len(exts):
            ext = exts[i]
            dependencies = self.res_classes_ext_map[ext].get_dependencies()

            # calculating dependency satisfaction
            if len(dependencies)==0:
                satisfied = True
            else:
                satisfactions = map(lambda dep: self.__normalize_extension(dep) in exts[:i], 
                            dependencies)
                satisfied = reduce(lambda x,y: x and y, satisfactions)
            
            # 
            if satisfied:
                i += 1
            else:
                if total_iter > len(exts)*2:
                    raise Exception("Circular dependency")
                exts.append(exts.pop(i))
            total_iter += 1
        return exts

    @property
    def sorted_extensions(self):
        """sorted depending on resources dependencies"""
        return self._get_sorted_extensions(str(self.resource_classes))

    @staticmethod
    def __normalize_extension(ext:str):
        ext = utils.normalize_extension(ext)
        return ext

    def add_plugin(self, plugin:Plugin):
        """
        adds plugin to `self.plugins`, 
        also adds all resource classes from *plugin* to `self.resource_classes` 
        and maps it by it's extensions to `self.res_classes_ext_map`
        """
        self.plugins.append(plugin)

        for res_class in plugin.resource_classes:
            if hasattr(res_class, "get_extensions"):
                self.resource_classes.add(res_class)
                Resource._give_subclass(res_class)
                extensions = res_class.get_extensions()
                for ext in extensions:
                    ext = self.__normalize_extension(ext)
                    self.res_classes_ext_map[ext] = res_class

    def get_res_class_by_ext(self, extension)->Type[Resource]:
        """
        returns resource class related to given *extension*.
        returns `None` if not found.
        """
        extension = self.__normalize_extension(extension)
        return self.res_classes_ext_map.get(extension, None)
    
    def get_res_class_by_filepath(self, filepath:Path)->Type[Resource]:
        """
        returns resource class related to extension of given *filepath*.
        returns `None` if not found.
        """
        ext = self.__normalize_extension(filepath.suffix)
        return self.get_res_class_by_ext(ext)

PLUGIN_TEMPLATES_DIR = CFD/"plugin_templates"

class PluginMaker():
    ADDITIONAL_TEMPLATES = [
        "using_blender_export"
    ]
    def __init__(self, id:str, using_blender_export=False) -> None:
        self.id = id
        self.using_blender_export = using_blender_export
        self.directory = PLUGINS_DIR/self.id
    
    def raise_if_unable_to_make(self):
        if self.directory.exists():
            raise Exception("plugin already exists")
        if self.directory.is_file():
            raise Exception("hmm, there is a file in a plugins folder, and it's named just like your id...") # why?

    def make_plugin(self):
        self.raise_if_unable_to_make()
        self.prepare_dir()
        self.apply_template("base")
        if self.using_blender_export:
            self.apply_template("blender_export")

    def edit_plugin(self):
        os.startfile(str(self.directory.resolve()))

    def prepare_dir(self):
        self.directory.mkdir(parents=True, exist_ok=True)

    def render_code(self, *lines):
        return "\n".join(lines).replace("\t ", "    ")
    
    def apply_template(self, id:str):
        template_dir = PLUGIN_TEMPLATES_DIR/id
        if not template_dir.exists() or not template_dir.is_dir():
            return

        for file in template_dir.rglob("*"):
            if not file.is_file(): continue
            dst_file = self.directory/file.relative_to(template_dir)
            utils.make_dirs_to_file(dst_file)
            dst_file.write_bytes(file.read_bytes())
