import argparse
from functools import cache, cached_property, reduce
import json
from os import stat
import os
from pathlib import Path
from threading import Lock, RLock
import time
from typing import Generator
import traceback
from typing import Type
import typing
from termcolor import colored

from .storable import PathField, Storable
from .resource_types.resource_base import ExportConfig, Resource
from . import utils
from serde import Model, fields
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .file_system import *

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class ResourcesRegistry:
    """
    provides and stores resources classes
    """
    def __init__(self) -> None:
        self.resource_classes = set()
        self.res_classes_ext_map = {}
        self.register_core_resources()
    
    def register_resources_in_dir(self, directory:Path):
        modules = utils.find_classes_in_dir(directory, Resource)
        for cls in modules:
            self.add_resource(cls)

    def register_resources_from_plugin(self, plugin_id:str):
        plugins_dir = CFD/"plugins"
        try:
            self.register_resources_in_dir(plugins_dir/plugin_id)
        except:
            traceback.print_exc()
            print(f"Failed to import plugin \"{plugin_id}\"")
    
    def register_core_resources(self):
        self.register_resources_in_dir(CFD/"resource_types")

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

    def add_resource(self, res_class):
        """
        adds *res_class* to `self.resource_classes` and maps it by it's extensions to `self.res_classes_ext_map`
        """
        if hasattr(res_class, "get_extensions"):
            self.resource_classes.add(res_class)
            Resource._give_subclass(res_class)
            extensions = res_class.get_extensions()
            for ext in extensions:
                ext = self.__normalize_extension(ext)
                self.res_classes_ext_map[ext] = res_class

    def get_res_class_by_ext(self, extension)->Type[Resource]:
        """
        returns resource class related to given *extension*
        """
        extension = self.__normalize_extension(extension)
        return self.res_classes_ext_map.get(extension, None)
    
    def get_res_class_by_filepath(self, filepath:Path)->Type[Resource]:
        """
        returns resource class related to extension of given *filepath*
        """
        ext = self.__normalize_extension(filepath.suffix)
        return self.get_res_class_by_ext(ext)

class TimerStatusPrinter():
    def __init__(self) -> None:
        self.start_time = datetime.datetime.now()
        self.message = ""

    def start_timer(self):
        self.start_time = datetime.datetime.now()

    def elapsed_time_str(self):
        now = datetime.datetime.now()
        elapsed_time = (now - self.start_time)
        s = utils.strfdelta(elapsed_time)
        return f"{s:>9}"

    def current_time(self):
        now = datetime.datetime.now()
        return now.strftime("%H:%M")
    
    def print_status(self, erase_last=True, end=""):
        s = f"| {self.message}... {self.current_time()} {self.elapsed_time_str()} |   "
        if erase_last: print("\r"+s, end=end)
        else: print(s)

class ExportArgsRegistry():
    def __init__(self) -> None:
        self.__files_args:dict[str, argparse.Namespace] = {}

    @staticmethod
    def _path_to_key(filepath:Path):
        return filepath.resolve().as_posix()
    
    def get_file_export_args(self, filepath:Path) -> argparse.Namespace:
        key = self._path_to_key(filepath)
        args = self.__files_args.get(key, None)
        if args is None:
            args = argparse.Namespace()
        return args

    def register_file_export_args(self, filepath:Path, args_dict:dict):
        key = self._path_to_key(filepath)
        args = self.__files_args.get(key, None)
        if args is None:
            args = argparse.Namespace()
        for arg_key in args_dict:
            setattr(args, arg_key, args_dict[arg_key])
        self.__files_args[key] = args
        
    def apply_export_json_file(self, export_json_file:Path):
        json_dir = export_json_file.parent.resolve()
        try:
            json_text = export_json_file.read_text()
            data = json.loads(json_text)
            files_export_args = data.get("files_export_args", {})
            for filepath_str in files_export_args:
                filepath = Path(filepath_str)
                if not filepath.is_absolute():
                    filepath = (json_dir / filepath).resolve()
                args_dict = files_export_args[filepath_str]
                self.register_file_export_args(filepath, args_dict)
        except:
            traceback.print_exc()

    def load_with_files_iterator(self, files_iterator:FilesInDirIterator):
        for filepath in files_iterator.iterate_files():
            if "".join(filepath.suffixes) == ".export.json":
                self.apply_export_json_file(filepath)

class ExporterConfig(ExportConfig):
    plugins: fields.List(fields.Str) = []

class ExportResult():
    def __init__(self, resource:Resource=None, success=False) -> None:
        self.resource:Resource = resource
        self.success:bool = success

class ResourcesExporter:
    def __init__(self, config:ExporterConfig=None) -> None:
        self.config = config
        if self.config is None:
            self.config = ExporterConfig.load_from_file(ExporterConfig, CWD/"exporter_config.json")
        
        self.files_iterator = FilesInDirIterator(self.config.raw_folder)
        self.resources_registry = ResourcesRegistry()
        self.resources_registry.register_core_resources()
        for plugin_id in self.config.plugins:
            self.resources_registry.register_resources_from_plugin(plugin_id)

        self.export_args_registry = ExportArgsRegistry()
        self.export_args_registry.load_with_files_iterator(self.files_iterator)

        self.config.save()

        self.observing_status_printer = TimerStatusPrinter()
    
    def print_exporting(self, filepath:Path):
        short_path = (filepath.relative_to(self.config.raw_folder).as_posix())
        print(f"exporting \"{filepath.suffix}\" resource: \"{short_path}\"...")

    def export_one_resource(self, filepath:Path):
        """ Instances Resource class and calls its `export` method"""    

        export_result = ExportResult()
        
        res_class = self.resources_registry.get_res_class_by_filepath(filepath)
        if res_class is None: return export_result

        resource = res_class(filepath, self.config)
        export_result.resource = resource

        try:
            export_args = self.export_args_registry.get_file_export_args(filepath)
            export_kwargs = dict(export_args._get_kwargs())
            resource.export(**export_kwargs)
            print(colored(f"exported {resource}", "green"))
            export_result.success = True

        except Exception as e:
            print(colored(f"failed to export {resource}", 'red'))
            if self.config.verbose: traceback.print_exc()
            else:
                print(" ".join(list(map(str, e.args))))
        
        return export_result
    
    def export_resources(self):
        """uses self.export_one_resource(res_path)"""
        results = []
        exts = self.resources_registry.sorted_extensions
        for ext in exts:
            for filepath in self.files_iterator.iterate_changed_files(ext=ext):
                result = self.export_one_resource(filepath)
                results.append(result)

                if result.success:
                    self.files_iterator.update_file_info(filepath)
        return results

    # observing
    _has_something_to_export = False
    observe_start_date = datetime.datetime.now()
    files_observer: Observer = None
    is_observing: Observer = None
    observe_print_status = True

    def start_observing_loop(self):
        print()
        self.start_observing()
        while self.is_observing:
            try:
                self.update_observer()
            except KeyboardInterrupt:
                self.stop_observing()
        print()

    def print_status(self):
        if not self.observe_print_status: return
        self.observing_status_printer.message = "observing"
        end = ""
        if self._has_something_to_export:
            self.observing_status_printer.message = "exporting"
            end = "\n"
        self.observing_status_printer.print_status(erase_last=True, end=end)

    def __del__(self):
        self.stop_observing()

    def _on_some_file_change(self):
        try:
            self.files_observer._lock.acquire()
            self._has_something_to_export = True
            self.files_observer._lock.release()
        except:
            traceback.print_exc()

    def start_observing(self):
        self.observe_start_date = datetime.datetime.now()
        self.observing_status_printer.start_timer()

        self.print_status()
        self.files_observer = Observer()
        event_handler = FileSystemCallbackEventHandler(self._on_some_file_change)
        self.files_observer.schedule(event_handler, str(self.config.raw_folder), recursive=True)
        self.files_observer.start()

        self._has_something_to_export = True
        self.is_observing = True

    def update_observer(self) -> typing.List[Resource]:
        """returns list of exporter resources"""
        self.print_status()
        resources = []
        if self._has_something_to_export:
            self._has_something_to_export = False
            resources = self.export_resources()
        return resources

    def stop_observing(self):
        self.is_observing = False
        if self.files_observer is not None:
            self.files_observer.stop()
            self.files_observer.join()

class FileSystemCallbackEventHandler(FileSystemEventHandler):
    def __init__(self, callback) -> None:
        self.callback = callback
    def on_modified(self, event):
        self.callback()
    def on_created(self, event):
        self.callback()
    def on_moved(self, event):
        self.callback()