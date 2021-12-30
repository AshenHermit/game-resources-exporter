from dataclasses import dataclass
from os import stat
from pathlib import Path
from typing import Generator
from serde import serialize, deserialize
from serde.json import to_json, from_json
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import Storable
from resources_exporter.resource_types.resource_base import ExportConfig, Resource
import resources_exporter.utils as utils

CWD = Path(__file__).parent.resolve()

@deserialize
@serialize
@dataclass
class FileInfo:
    mtime: float

    def __init__(self, mtime=None, filepath:Path=None) -> None:
        self.mtime = mtime
        self.filepath = filepath

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

@deserialize
@serialize
@dataclass
class FilesRegistry(Storable):
    registry: dict[str, FileInfo]

    def __init__(self, registry=None, storage_file:Path=None) -> None:
        super().__init__(storage_file=storage_file)
        self.registry = registry or {}
        self.load()

    def get_file_info(self, filepath:Path)->FileInfo:
        filepath = Path(filepath).resolve()
        key = filepath.as_posix()
        info = None
        if key in self.registry:
            info = self.registry[key]
        else:
            info = self.update_file_info(filepath)
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
        self.files_registry = FilesRegistry(storage_file=storage_file)
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

class ResourcesRegistry:
    def __init__(self) -> None:
        self.resource_classes = set()
        self.res_classes_ext_map = {}
        self.register_available_resources()

    def register_available_resources(self):
        modules = utils.find_classes_in_dir(CWD/"resource_types", Resource)
        for cls in modules:
            self.add_resource(cls)

    @staticmethod
    def __normalize_extension(ext:str):
        ext = ext.replace(".", "")
        return ext

    def add_resource(self, res_class):
        if hasattr(res_class, "get_extensions"):
            self.resource_classes.add(res_class)
            extensions = res_class.get_extensions()
            for ext in extensions:
                ext = self.__normalize_extension(ext)
                self.res_classes_ext_map[ext] = res_class

    def get_res_class_by_ext(self, extension)->Type[Resource]:
        extension = self.__normalize_extension(extension)
        return self.res_classes_ext_map.get(extension, None)
    
    def get_res_class_by_filepath(self, filepath:Path)->Type[Resource]:
        ext = self.__normalize_extension(filepath.suffix)
        return self.get_res_class_by_ext(ext)

class ResourcesExporter:
    def __init__(self, config:ExportConfig=None) -> None:
        self.config = config or ExportConfig()
        self.files_iterator = FilesInDirIterator(self.config.raw_folder)
        self.resources_registry = ResourcesRegistry()
    
    def export_resources(self):
        for filepath in self.files_iterator.iterate_changed_files():
            self.export_one_resource(filepath)
            self.files_iterator.update_file_info(filepath)

    def print_exporting(self, filepath:Path):
        short_path = (filepath.relative_to(self.config.raw_folder).as_posix())
        print(f"exporting \"{filepath.suffix}\" resource: {short_path}")

    def export_one_resource(self, filepath:Path):
        res_class = self.resources_registry.get_res_class_by_filepath(filepath)
        if res_class is None: return

        self.print_exporting(filepath)
        resource = res_class(filepath, self.config)
        resource.export()
        return resource

def main():
    config = ExportConfig(storage_file=CWD/"config.json")
    exporter = ResourcesExporter(config)
    exporter.export_one_resource()

if __name__ == '__main__':
    main()
