import json
from pathlib import Path
from typing import Generator
from serde import Model, fields
import traceback
from typing import Type
from serde.exceptions import ContextError, add_context

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
        if (PathField._relative_to / value).exists():
            return (PathField._relative_to / value).resolve()
        return Path(value).resolve()

class Storable(Model):
    """Storing class instance to json. Also stores all fields not defined with `serde.fields` and without underscore "_" at the beginning of field name"""
    def __init__(self, _storage_file:Path=None, **kwargs) -> None:
        if _storage_file is None:
            _storage_file = CFD / (self.__class__.__name__+".json")
        self._storage_file = Path(_storage_file)
        self.__dict__.update(kwargs)

    def get(self, key:str, default, save_if_attr_is_new=False):
        if not hasattr(self, key):
            if save_if_attr_is_new:
                setattr(self, key, default)
                self.save()
        return getattr(self, key, default)

    def tune_path_field(self):
        PathField._relative_to = self._storage_file.parent
    
    def load(self):
        """ returns `self`, if the `_storage_file` exists, loads data into itself """
        self.tune_path_field()
        loading_key = "___something_is_loading"
        if getattr(Storable, loading_key, False):
            return None

        # blocking recursion
        setattr(Storable, loading_key, True)
        
        cls = self.__class__
        if self._storage_file.exists():

            json_string = self._storage_file.read_text(
                encoding='utf-8')
            try:
                data_dict = json.loads(json_string)
            except:
                raise Exception("cant load json")
            instance = cls.from_dict(data_dict)
            _storage_file = self._storage_file
            self.__dict__.update(instance.__dict__)
            self._storage_file = _storage_file

        # unblocking
        setattr(Storable, loading_key, False)

        return self
    
    @classmethod
    def load_from_file(cls, storage_file:Path):
        instance:Storable = cls(_storage_file=storage_file)
        instance.load()
        return instance

    @classmethod
    def from_dict(cls, d:dict):
        """
        Convert a dictionary to an instance of this model.

        Args:
            d (dict): a serialized version of this model.

        Returns:
            Model: an instance of this model.
        """
        model:object = cls.__new__(cls)
        model.__dict__.update(d)

        model_cls = None
        tag = model.__class__.__tag__
        while tag and model_cls is not model.__class__:
            model_cls = model.__class__
            with add_context(tag):
                model, d = tag._deserialize_with(model, d)
            tag = model.__class__.__tag__

        for field in reversed(model.__class__.__fields__.values()):
            with add_context(field):
                model, d = field._deserialize_with(model, d)

        model._normalize()
        model._validate()

        return model


    def to_dict(self):
        data_dict:dict = self.__dict__.copy()
        for k in list(data_dict.keys()):
            if k.startswith("_"):
                data_dict.pop(k)
        data_dict.update(super().to_dict())
        return data_dict

    def save(self):
        self.tune_path_field()
        data_dict:dict = self.to_dict()
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

