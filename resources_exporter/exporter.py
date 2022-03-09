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

from .resources_registry import ResourcesRegistry

from .resource_types.plugin import Plugin

from .storable import PathField, Storable
from .resource_types.resource_base import ExportConfig, Resource
from .resource_types.res_local_config import *
from . import utils
from serde import Model, fields
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .file_system import *

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

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
    def __init__(self, resource:Resource=None, success=False, out_log:str=None, error_log:str=None, date:datetime.datetime=None) -> None:
        self.resource:Resource = resource
        self.success:bool = success
        self.out_log:str = out_log or ""
        self.error_log:str = error_log or ""
        self.date:datetime.datetime = date

class ResourcesExporter:
    @staticmethod
    def get_config_path(project_dir:Path):
        return project_dir/"exporter_config.json"

    def __init__(self, config:ExporterConfig=None, project_dir:Path=None) -> None:
        self.project_dir = project_dir or CWD
        self.project_dir = Path(self.project_dir)
        self.config = config
        if self.config is None:
            self.config = ExporterConfig.load_from_file(ResourcesExporter.get_config_path(self.project_dir))
        
        self.files_iterator = FilesInDirIterator(self.config.raw_folder, self.project_dir)
        self.resources_registry = ResourcesRegistry()
        self.resources_registry.register_core_plugin()
        for plugin_id in self.config.plugins:
            self.resources_registry.register_plugin(plugin_id)

        self.export_args_registry = ExportArgsRegistry()
        self.export_args_registry.load_with_files_iterator(self.files_iterator)

        self.files_to_export_queue:typing.List[Path] = []

        self.config.save()

        self.observing_status_printer = TimerStatusPrinter()
    
    def print_exporting(self, filepath:Path):
        short_path = (filepath.relative_to(self.config.raw_folder).as_posix())
        print(f"exporting \"{filepath.suffix}\" resource: \"{short_path}\"...")

    def run_resource_command(self, filepath:Path, cmd_id:str):
        res_class = self.resources_registry.get_res_class_by_filepath(filepath)
        if res_class is None: return
        resource = res_class(filepath, self.config)
        for cmd in res_class.get_commands():
            if cmd.id == cmd_id:
                try:
                    cmd.func(resource)
                except Exception as e:
                    if self.config.verbose: traceback.print_exc()
                    else: print(" ".join(list(map(str, e.args))))
                return

    def export_one_resource(self, filepath:Path):
        """ Instances Resource class and calls its `export` method"""    

        export_result = ExportResult()
        export_result.date = datetime.datetime.now()
        
        res_class = self.resources_registry.get_res_class_by_filepath(filepath)
        if res_class is None: return export_result

        resource = res_class(filepath, self.config)
        export_result.resource = resource

        with utils.StdoutSplitter.context() as stdout_splitter:
            try:
                export_args = ResLocalConfig.s_get_settings_for_file(filepath)
                export_kwargs = export_args.to_dict()
                resource.export(**export_kwargs)
                print(colored(f"exported {resource}", "green"))
                export_result.success = True

            except Exception as e:
                if self.config.verbose:
                    print(colored(str(e), 'red'))
                    traceback.print_exc()
                else:
                    print(" ".join(list(map(str, e.args))))
                
                print(colored(f"failed to export {resource}", 'red'))
                export_result.error_log = str(e)
            
            export_result.out_log = stdout_splitter.read()
            
        print(export_result.out_log)
        
        return export_result
    
    def export_resources(self):
        """uses self.export_one_resource(res_path)"""
        results = []
        exts = self.resources_registry.sorted_extensions
        for ext in exts:
            for filepath in self.files_iterator.iterate_changed_files(ext=ext):
                result = self.export_one_resource(filepath)
                if result is None:
                    self.files_iterator.update_file_info(filepath)
                else:
                    results.append(result)
                    if result.success:
                        self.files_iterator.update_file_info(filepath)
        ResLocalConfig.clear_cache()
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

    def _on_some_file_change(self, file:Path):
        try:
            with self.files_observer._lock:
                self.files_to_export_queue.append(file)
        except:
            traceback.print_exc()

    def start_observing(self, export_all_on_start=True):
        self.observe_start_date = datetime.datetime.now()
        self.observing_status_printer.start_timer()

        if export_all_on_start: self.export_resources()

        self.print_status()
        self.files_observer = Observer()
        def _fs_obj_change(path:str):
            path:Path = Path(path).resolve()
            if path.name == ResLocalConfig._CONFIG_FILENAME: return
            if path.is_file():
                self._on_some_file_change(path)
            elif path.is_dir():
                for file in path.rglob("*.*"):
                    self._on_some_file_change(file)
        event_handler = FileSystemCallbackEventHandler(_fs_obj_change)
        self.files_observer.schedule(event_handler, str(self.config.raw_folder), recursive=True)
        self.files_observer.start()

        self.is_observing = True

    def update_observer(self) -> typing.List[Resource]:
        """returns list of exporter resources"""
        self.print_status()
        resources = []

        with self.files_observer._lock:
            while len(self.files_to_export_queue)>0:
                file = self.files_to_export_queue.pop()
                if self.files_iterator.files_registry.is_file_changed(file):
                    cfg = ResLocalConfig.s_get_settings_for_file(file)
                    if not cfg.get("observer_ignore", False):
                        res = self.export_one_resource(file)
                        self.files_iterator.files_registry.update_file_info(file)
                        resources.append(res)
            ResLocalConfig.clear_cache()
        
        return resources

    def stop_observing(self):
        self.is_observing = False
        if self.files_observer is not None:
            self.files_observer.stop()
            self.files_observer.join()

    def init_workspace(self, for_cli=False):
        self.config.save()

        bat_file = self.project_dir / "run_resources_exporter.bat"
        if not bat_file.exists():
            if for_cli:
                script = (CFD/'../exporter_cli.py').resolve()
                bat_text = f"python \"{script}\" observe" + "\n"
                bat_text += "pause"
            else:
                script = (CFD/'../exporter.py').resolve()
                bat_text = f"python \"{script}\"" + "\n"
            print(colored(f"writed \"{bat_file.name}\", you can run exporter with it", "green"))
            bat_file.write_text(bat_text)

class FileSystemCallbackEventHandler(FileSystemEventHandler):
    def __init__(self, callback) -> None:
        self.callback = callback
    def on_modified(self, event):
        self.callback(event.src_path)
    def on_created(self, event):
        self.callback(event.src_path)
    def on_moved(self, event):
        self.callback(event.src_path)