
import os
from pathlib import Path
from typing import Generator

from .storable import PathField, Storable
from serde import Model, fields

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
        if new_info is None: return True
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
    def __init__(self, directory: Path, storage_dir: Path) -> None:
        storage_file = storage_dir / "files_registry.json"
        self.files_registry = FilesRegistry(_storage_file=storage_file)
        self.files_registry.load()
        self.directory = directory

    def iterate_files(self, ext=None) -> Generator[Path, None, None]:
        pattern = "*"
        if ext is not None: pattern = "*."+ext

        for filepath in self.directory.rglob(pattern):
            if filepath.is_file():
                yield filepath
    
    def iterate_changed_files(self, ext=None):
        for filepath in self.iterate_files(ext=ext):
            if self.files_registry.is_file_changed(filepath):
                yield filepath
    
    def update_file_info(self, filepath:Path):
        self.files_registry.update_file_info(filepath)
        self.files_registry.save()