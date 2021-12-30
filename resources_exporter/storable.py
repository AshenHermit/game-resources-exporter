from dataclasses import dataclass
from os import stat
from pathlib import Path
from typing import Generator
from serde import serialize, deserialize
from serde.json import to_json, from_json
import traceback
from typing import Type

CWD = Path(__file__).parent.resolve()

@deserialize
@serialize
@dataclass
class Storable():
    """storing class instance to json"""
    def __init__(self, storage_file:Path=None) -> None:
        if storage_file is None:
            storage_file = CWD / (self.__class__.__name__+".json")
        self.storage_file = Path(storage_file)
    
    def load(self):
        loading_key = "something_is_loading"
        if getattr(Storable, loading_key, False):
            return None

        # blocking recursion
        setattr(Storable, loading_key, True)
        
        cls = self.__class__
        if not self.storage_file.exists(): 
            return cls()
        
        json_string = self.storage_file.read_text(
            encoding='utf-8')
        instance = from_json(cls, json_string)
        self.__dict__.update(instance.__dict__)

        # unblocking
        setattr(Storable, loading_key, False)

        return instance

    @staticmethod
    def load_from_file(cls, storage_file:Path):
        instance = cls(storage_file=storage_file)
        instance.load()
        return instance

    def save(self):
        json_string = to_json(self)
        try:
            self.storage_file.write_text(
                json_string,
                encoding='utf-8')
            return True
        except:
            traceback.print_exc()
            return False