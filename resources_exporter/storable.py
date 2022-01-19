from os import stat
from pathlib import Path
from typing import Generator
from serde import Model, fields
import traceback
from typing import Type

CFD = Path(__file__).parent.resolve()

class PathField(fields.Field):
    def serialize(self, value):
        return str(value)
    def deserialize(self, value):
        return Path(value)


class Storable(Model):
    """storing class instance to json"""
    def __init__(self, _storage_file:Path=None, **kwargs) -> None:
        if _storage_file is None:
            _storage_file = CFD / (self.__class__.__name__+".json")
        self._storage_file = Path(_storage_file)
        self.__dict__.update(kwargs)
    
    def load(self):
        loading_key = "something_is_loading"
        if getattr(Storable, loading_key, False):
            return None

        # blocking recursion
        setattr(Storable, loading_key, True)
        
        cls = self.__class__
        if not self._storage_file.exists(): 
            return self
        
        json_string = self._storage_file.read_text(
            encoding='utf-8')
        instance = cls.from_json(json_string)
        _storage_file = self._storage_file
        self.__dict__.update(instance.__dict__)
        self._storage_file = _storage_file

        # unblocking
        setattr(Storable, loading_key, False)

        return self
    
    @staticmethod
    def load_from_file(cls, storage_file:Path):
        instance = cls(_storage_file=storage_file)
        instance.load()
        return instance

    def save(self):
        json_string = self.to_json(indent=2)
        try:
            if not hasattr(self, "_storage_file"): return False
            self._storage_file.write_text(
                json_string,
                encoding='utf-8')
            return True
        except:
            traceback.print_exc()
            return False

