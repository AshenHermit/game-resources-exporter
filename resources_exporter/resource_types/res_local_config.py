from functools import cache
import typing
from ..storable import Storable
from pathlib import Path
from serde import Model, fields
import fnmatch

class ResLocalSettings(Storable):
    def __init__(self, res_local_config, **kwargs) -> None:
        super().__init__(None, **kwargs)
        self._res_local_config = res_local_config

    def save(self):
        # for k in self.__dict__:
        #     if 
        self._res_local_config.save()

class ResLocalConfig(Storable):
    _CONFIG_FILENAME = ".local.cfg"
    settings_map = fields.Dict(str, ResLocalSettings)

    def __init__(self, _storage_file: Path = None, **kwargs) -> None:
        super().__init__(_storage_file, **kwargs)
        self.settings_map:typing.Dict[str, ResLocalSettings] = {}

    def get_settings_for_file(self, file:Path):
        settings = ResLocalSettings(self)
        if not file.exists(): return None
        if file.resolve().as_posix().startswith(self._storage_file.parent.resolve().as_posix()):
            rel_path = file.relative_to(self._storage_file.parent)
            path_str = rel_path.as_posix()
            for rule in self.settings_map.keys():
                if fnmatch.fnmatch(path_str, rule):
                    settings.__dict__.update(self.settings_map[rule].__dict__)
        return settings

    def get_settings_for_rule(self, rule:str):
        if rule not in self.settings_map:
            self.settings_map[rule] = ResLocalSettings(self)
        return self.settings_map[rule]

    def remove_rule(self, rule:str):
        self.settings_map.pop(rule)

    @staticmethod
    @cache
    def of_filepath(path:Path):
        if path.is_file():
            directory = path.parent
        elif path.is_dir():
            directory = path
        else: return ResLocalConfig()
        cfg_filepath = directory / ResLocalConfig._CONFIG_FILENAME
        cfg:ResLocalConfig = ResLocalConfig.load_from_file(cfg_filepath)
        if cfg is None: cfg = ResLocalConfig()
        return cfg

    @classmethod
    def clear_cache(cls):
        cls.of_filepath.cache_clear()

    @classmethod
    def s_get_settings_for_file(cls, path:Path):
        cfg = cls.of_filepath(path)
        settings = cfg.get_settings_for_file(path)
        if settings is None: settings = ResLocalSettings(cfg)
        return settings