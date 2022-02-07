from os import stat
import os
from pathlib import Path
from typing import Generator
import traceback
from typing import Type, TypeVar
from resources_exporter.storable import Storable
from resources_exporter.resource_types.resource_base import Resource
import resources_exporter.utils as utils
from resources_exporter.exporter import ResourcesExporter, ExporterConfig

import argparse

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class Args:
    parser_help:str = ""

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    @staticmethod
    def path_factory(value:str):
        return Path(value).expanduser().resolve()
    
    @staticmethod
    def add_args_to_argparser(argparser:argparse.ArgumentParser):
        pass

class ExportOneResArgs(Args):
    parser_help:str = "export one resource"

    def __init__(self, **kwargs) -> None:
        self.file:Path = Path("")
        super().__init__(**kwargs)

    @staticmethod
    def add_args_to_argparser(argparser:argparse.ArgumentParser):
        argparser.add_argument("-f", "--file", type=Args.path_factory)

class InitArgs(Args):
    parser_help:str = "init exporter workspace, setup config"

class ObserveArgs(Args):
    parser_help:str = "start observing files changes to export them"

class ExportAllResArgs(Args):
    parser_help:str = "export all resources"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class ResourcesExporterCLI():
    def __init__(self) -> None:
        self.config = ExporterConfig.load_from_file(ExporterConfig, CWD/"exporter_config.json")
        self.resources_exporter = ResourcesExporter(self.config)

    def export_one_resource(self, args:ExportOneResArgs):
        self.resources_exporter.export_one_resource(args.file)
    
    def export_resources(self, args:ExportAllResArgs):
        self.resources_exporter.export_resources()

    def init_workspace(self, args:InitArgs):
        self.resources_exporter.config.save()

    def start_observing(self, args:ObserveArgs):
        self.resources_exporter.start_observing()

    def make_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(help="sub-command help")

        commands = {
            "one": (ExportOneResArgs, self.export_one_resource),
            "all": (ExportAllResArgs, self.export_resources),
            "init": (InitArgs, self.init_workspace),
            "observe": (ObserveArgs, self.start_observing),
        }
        for key in commands:
            args_cls, func = commands[key]
            help = args_cls.parser_help
            sparser = subparsers.add_parser(key, help=help)
            args_cls.add_args_to_argparser(sparser)
            sparser.set_defaults(func=func)
            sparser.set_defaults(args_cls=args_cls)

        return parser
    
    def run(self):
        parser = self.make_parser()
        args = parser.parse_args()
        if hasattr(args, "func"):
            if hasattr(args, "args_cls"):
                args = args.args_cls(**args.__dict__)
            args.func(args)
        else:
            parser.print_help()

def main():
    cli = ResourcesExporterCLI()
    cli.run()

if __name__ == '__main__':
    main()
