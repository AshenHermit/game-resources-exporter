import argparse
import json
from os import stat
import os
from pathlib import Path
import time
from tracemalloc import start
from turtle import Turtle
from typing import Generator
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import PathField, Storable
from resources_exporter.resource_types.resource_base import ExportConfig, Resource
import resources_exporter.utils as utils
from serde import Model, fields
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class FileInfo(Model):
    mtime: float
    filepath: PathField

    def __init__(self, mtime=None, filepath:Path=None) -> None:
        self.mtime:float = mtime or 0.0
        self.filepath:Path = filepath

    def is_file_changed(self)->bool:
        new_info = FileInfo.from_file(self.filepath)
        if new_info.mtime > self.mtime:
            return True
        else:
            return False

    @staticmethod
    def from_file(filepath:Path):
        filepath = Path(filepath)
        if not filepath.exists(): return None

        fileinfo = FileInfo(None, filepath)
        stat = filepath.stat()
        fileinfo.mtime = stat.st_mtime
        return fileinfo

class FilesRegistry(Storable):
    registry: fields.Dict(str, FileInfo)

    def __init__(self, registry=None, _storage_file:Path=None, **kwargs) -> None:
        self.registry = registry or {}
        super().__init__(_storage_file=_storage_file, **kwargs)

    def get_file_info(self, filepath:Path)->FileInfo:
        filepath = Path(filepath).resolve()
        key = filepath.as_posix()
        info = None
        if key in self.registry:
            info = self.registry[key]
        return info

    def is_file_changed(self, filepath:Path)->bool:
        filepath = Path(filepath).resolve()
        info = self.get_file_info(filepath)
        if info:
            return info.is_file_changed()
        return True

    def update_file_info(self, filepath:Path):
        filepath = Path(filepath).resolve()
        if filepath.exists():
            fileinfo = FileInfo.from_file(filepath)
            if fileinfo:
                key = filepath.as_posix()
                self.registry[key] = fileinfo
                return fileinfo
        return None

class FilesInDirIterator:
    def __init__(self, directory: Path) -> None:
        storage_file = CWD / "files_registry.json"
        self.files_registry = FilesRegistry(_storage_file=storage_file)
        self.files_registry.load()
        self.directory = directory

    def iterate_files(self) -> Generator[Path, None, None]:
        for filepath in self.directory.glob("**/*"):
            if filepath.is_file():
                yield filepath
    
    def iterate_changed_files(self):
        for filepath in self.iterate_files():
            if self.files_registry.is_file_changed(filepath):
                yield filepath
    
    def update_file_info(self, filepath:Path):
        self.files_registry.update_file_info(filepath)
        self.files_registry.save()

class ResourcesRegistry:
    """
    provides and stores resources classes
    """
    def __init__(self) -> None:
        self.resource_classes = set()
        self.res_classes_ext_map = {}
        self.register_core_resources()

    def register_core_resources(self):
        modules = utils.find_classes_in_dir(CFD/"resource_types", Resource)
        for cls in modules:
            self.add_resource(cls)

    @staticmethod
    def __normalize_extension(ext:str):
        ext = ext.lower()
        ext = ext.replace(".", "")
        return ext

    def add_resource(self, res_class):
        """
        adds *res_class* to `self.resource_classes` and maps it to it's extensions to `self.res_classes_ext_map`
        """
        if hasattr(res_class, "get_extensions"):
            self.resource_classes.add(res_class)
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

class ResourcesExporter:
    def __init__(self, config:ExportConfig=None) -> None:
        self.config = config or ExportConfig()
        self.files_iterator = FilesInDirIterator(self.config.raw_folder)
        self.resources_registry = ResourcesRegistry()
        self.resources_registry.register_core_resources()

        self.export_args_registry = ExportArgsRegistry()
        self.export_args_registry.load_with_files_iterator(self.files_iterator)

        self.config.save()
    
    def print_exporting(self, filepath:Path):
        short_path = (filepath.relative_to(self.config.raw_folder).as_posix())
        print(f"exporting \"{filepath.suffix}\" resource: \"{short_path}\"...")

    def export_one_resource(self, filepath:Path):
        """ Instances Resource class and calls its `export` method"""    
        
        res_class = self.resources_registry.get_res_class_by_filepath(filepath)
        if res_class is None: return None

        # self.print_exporting(filepath)
        resource = res_class(filepath, self.config)
        try:
            export_args = self.export_args_registry.get_file_export_args(filepath)
            export_kwargs = dict(export_args._get_kwargs())
            resource.export(**export_kwargs)
            print(f"exported {resource}")
        except:
            print(f"failed to export {resource}")
            if self.config.verbose: traceback.print_exc()
        return resource
    
    def export_resources(self):
        resources = []
        for filepath in self.files_iterator.iterate_changed_files():
            res = self.export_one_resource(filepath)
            if res is not None:
                resources.append(res)
            self.files_iterator.update_file_info(filepath)
        return resources

    def start_observing(self):
        print()

        start_date = datetime.datetime.now()

        def elapsed_time_str():
            now = datetime.datetime.now()
            elapsed_time = (now - start_date)
            s = utils.strfdelta(elapsed_time)
            return f"{s:>9}"
            
        def print_status(erase_last=True):
            s = f"| observing changes... {elapsed_time_str()} |   "
            if erase_last: print("\r"+s, end="")
            else: print(s)

        resources = self.export_resources()
        print_status()
        
        should_close = False
        def on_change():
            try:
                resources = self.export_resources()
                if len(resources)>0:
                    pass
            except:
                traceback.print_exc()

        event_handler = FileSystemCallbackEventHandler(on_change)
        observer = Observer()
        observer.schedule(event_handler, str(self.config.raw_folder), recursive=True)
        observer.start()
        while not should_close:
            try:
                print_status()
                time.sleep(1)
            except KeyboardInterrupt:
                should_close = True
        observer.stop()
        observer.join()

        print()

class FileSystemCallbackEventHandler(FileSystemEventHandler):
    def __init__(self, callback) -> None:
        self.callback = callback
    def on_modified(self, event):
        self.callback()
    def on_created(self, event):
        self.callback()
    def on_moved(self, event):
        self.callback()