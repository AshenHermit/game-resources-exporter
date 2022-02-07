import json
from os import stat
from pathlib import Path
from typing import Generator
from serde import Model, fields
import traceback
from typing import Type

CFD = Path(__file__).parent.resolve()

class PathField(fields.Field):
    _relative_to = CFD
    def serialize(self, value):
        if hasattr(value, "relative_to"):
            try:
                value = value.relative_to(PathField._relative_to)
            except: pass
            value = value.as_posix()
        return str(value)
    def deserialize(self, value):
        return Path(value).resolve()

class Storable(Model):
    """storing class instance to json"""
    def __init__(self, _storage_file:Path=None, **kwargs) -> None:
        if _storage_file is None:
            _storage_file = CFD / (self.__class__.__name__+".json")
        self._storage_file = Path(_storage_file)
        self.__dict__.update(kwargs)

    def get(self, key:str, default, save_if_attr_is_new=False):
        if not hasattr(self, key):
            setattr(self, key, default)
            if save_if_attr_is_new: self.save()
        return getattr(self, key, default)

    def tune_path_field(self):
        PathField._relative_to = self._storage_file.parent
    
    def load(self):
        self.tune_path_field()
        loading_key = "___something_is_loading"
        if getattr(Storable, loading_key, False):
            return None

        # blocking recursion
        setattr(Storable, loading_key, True)
        
        cls = self.__class__
        if not self._storage_file.exists(): 
            return self

        json_string = self._storage_file.read_text(
            encoding='utf-8')
        data_dict = json.loads(json_string)
        instance = cls.from_dict(data_dict)
        _storage_file = self._storage_file
        self.__dict__.update(data_dict)
        self.__dict__.update(instance.__dict__)
        self._storage_file = _storage_file

        # unblocking
        setattr(Storable, loading_key, False)

        return self
    
    @staticmethod
    def load_from_file(cls, storage_file:Path):
        instance:Storable = cls(_storage_file=storage_file)
        instance.load()
        return instance

    def save(self):
        self.tune_path_field()
        data_dict:dict = self.__dict__.copy()
        data_dict.update(self.to_dict())
        for k in list(data_dict.keys()):
            if k.startswith("_"): data_dict.pop(k)
        json_string = json.dumps(data_dict, indent=2)
        try:
            if not hasattr(self, "_storage_file"): return False
            self._storage_file.write_text(
                json_string,
                encoding='utf-8')
            return True
        except:
            traceback.print_exc()
            return False

