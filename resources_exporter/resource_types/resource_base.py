from dataclasses import dataclass
from os import stat
from pathlib import Path
from typing import Generator
from serde import serialize, deserialize
from serde.json import to_json, from_json
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import Storable

CWD = Path(__file__).parent.resolve()

@deserialize
@serialize
@dataclass
class ExportConfig(Storable):
    raw_folder: Path
    output_folder: Path
    output_root: Path
    verbose: False
    image_magic_cmd: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.raw_folder = Path("resources")
        self.output_folder = Path("output")
        self.output_root = Path("")
        self.verbose = False
        self.image_magic_cmd = "convert"

        self.__dict__.update(kwargs)

class ExportError(Exception):
    def __init__(self, filepath, message) -> None:
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)
    def __str__(self) -> str:
        return f"Failed to export a resource \"{self.filepath}\" : {self.message}"

class Resource:
    def __init__(self, filepath:Path, config:ExportConfig=None) -> None:
        self.filepath = filepath
        self.config = config or ExportConfig()

    def export(self):
        pass

    @staticmethod
    def get_extensions():
        return ["json"]
