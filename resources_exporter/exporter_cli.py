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
from resources_exporter.exporter import ResourcesExporter

import argparse

CWD = Path(__file__).parent.resolve()

class Args:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
    
    @staticmethod
    def add_args_to_argparser(argparser:argparse.ArgumentParser):
        pass

class ExportOneResArgs(Args):
    def __init__(self, **kwargs) -> None:
        self.file:Path = Path("")
        super().__init__(**kwargs)

    @staticmethod
    def add_args_to_argparser(argparser:argparse.ArgumentParser):
        argparser.add_argument("-f", "--file", type=utils.resolved_path)

class ExportAllResArgs(Args):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class ResourcesExporterCLI():
    def __init__(self) -> None:
        self.config = ExportConfig.load_from_file(ExportConfig, CWD/"config.json")
        self.resources_exporter = ResourcesExporter(self.config)

    def export_one_resource(self, args):
        pass
    
    def export_resources(self, args):
        pass

    def run(self):
        args = self.parse_args()
        args.func(args)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        
        subparsers = parser.add_subparsers(help="sub-command help")
        one_res_parser = subparsers.add_parser("export_one_resource")
        one_res_parser.set_defaults(func=self.export_one_resource)
        
        all_res_parser = subparsers.add_parser("export_one_resource")
        all_res_parser.set_defaults(func=self.export_resources)
        subparsers.add_parser("export_resources")
        args = parser.parse_args()
        return args

def main():
    config = ExportConfig(storage_file=CWD/"config.json")
    exporter = ResourcesExporter(config)
    exporter.export_one_resource()

if __name__ == '__main__':
    main()
