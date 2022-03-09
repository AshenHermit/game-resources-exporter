from os import stat
import os
from pathlib import Path
from typing import Generator
import traceback
from typing import Type, TypeVar
from .storable import Storable
from .resource_types.resource_base import Resource
from . import utils
from .exporter import ResourcesExporter, ExporterConfig
from .resources_registry import PluginMaker

import colorama

import argparse

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

def path_factory(value:str):
    return Path(value).expanduser().resolve()

class ActionUnit():
    parser_id:str = "action"
    parser_help:str = "base action class"
    def __init__(self, res_exporter:ResourcesExporter) -> None:
        self.res_exporter:ResourcesExporter = res_exporter
    def apply_kwargs(self, **kwargs):
        self.__dict__.update(kwargs)
    def add_args_to_argparser(self, argparser:argparse.ArgumentParser):
        pass
    def run(self):
        pass

class ExportOneRes(ActionUnit):
    parser_id:str = "one"
    parser_help:str = "export one resource"
    file:Path = Path("")
    def add_args_to_argparser(self, argparser:argparse.ArgumentParser):
        argparser.add_argument("-f", "--file", type=path_factory)
    def run(self):
        self.res_exporter.export_one_resource(self.file)

class ExportAllRes(ActionUnit):
    parser_id:str = "all"
    parser_help:str = "export all resources"
    def run(self):
        self.res_exporter.export_resources()

class InitExporter(ActionUnit):
    parser_id:str = "init"
    parser_help:str = "init exporter workspace: setup config, make batch file to run exporter"
    for_gui:bool = False
    def add_args_to_argparser(self, argparser:argparse.ArgumentParser):
        argparser.add_argument("-gui", "--for-gui", action="store_true")
    def run(self):
        self.res_exporter.init_workspace(not self.for_gui)

class Observe(ActionUnit):
    parser_id:str = "observe"
    parser_help:str = "start observing files changes to export them"
    def run(self):
        self.res_exporter.start_observing_loop()

class MakePluginAction(ActionUnit):
    parser_id:str = "new_plugin"
    parser_help:str = "make new plugin"
    id:str = "new_plugin"
    use_blend_export:bool = False
    def add_args_to_argparser(self, argparser:argparse.ArgumentParser):
        argparser.add_argument("id", type=str)
        argparser.add_argument("-blend", "--use-blend-export", action='store_true')
    def run(self):
        pm = PluginMaker(self.id, self.use_blend_export)
        pm.make_plugin()
        pm.edit_plugin()

class ResourcesExporterCLI():
    def __init__(self) -> None:
        self.resources_exporter = ResourcesExporter()
        self.actions = []

    def make_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(help="sub-command help")

        for subcls in ActionUnit.__subclasses__():
            action = subcls(self.resources_exporter)
            sparser = subparsers.add_parser(action.parser_id, help=action.parser_help)
            action.add_args_to_argparser(sparser)
            self.actions.append(action)
            sparser.set_defaults(action_instance=action)

        return parser
    
    def run(self):
        parser = self.make_parser()
        args = parser.parse_args()
        if hasattr(args, "action_instance"):
            action:ActionUnit = args.action_instance
            action.apply_kwargs(**args.__dict__)
            action.run()
        else:
            parser.print_help()

def main():
    colorama.init()
    
    cli = ResourcesExporterCLI()
    cli.run()

if __name__ == '__main__':
    main()
