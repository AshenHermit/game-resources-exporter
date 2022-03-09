from pathlib import Path
from PyQt5.QtCore import QSettings
import typing

class HandySettings():
    def __init__(self, organization: str, application: str):
        self._settings = QSettings(organization, application)
    
    def __getattr__(self, name: str) -> typing.Any:
        if name == "_settings": return super().__getattribute__(name)
        return self._settings.value(name, None)
    
    def __setattr__(self, name: str, value: typing.Any) -> None:
        if name == "_settings": super().__setattr__(name, value)
        self._settings.setValue(name, value)

    def get_projects_paths(self, type=Path):
        strings = self._settings.value("projects_list", [], str)
        paths = list(map(lambda x: type(x), strings))
        paths = list(filter(lambda x: Path(x).exists(), paths))
        return paths
    def set_projects_paths(self, paths:list[Path]):
        strings = list(map(lambda x: str(x), paths))
        self._settings.setValue("projects_list", strings)
    
    def remove_project(self, path:Path):
        paths = self.get_projects_paths(str)
        spath = str(path)
        idx = paths.index(spath)
        if idx != -1:
            paths.pop(idx)
        self.set_projects_paths(paths)

    def use_project(self, path:Path):
        paths = self.get_projects_paths(str)
        spath = str(path)
        if spath in paths:
            idx = paths.index(spath)
            if idx != -1:
                paths.pop(idx)
        paths.insert(0, spath)
        self.set_projects_paths(paths)
        

storage = HandySettings('Hermit', 'Resources Exporter')