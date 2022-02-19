import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

import threading
import time

from ..exporter import ExporterConfig, ResourcesExporter
from .. import utils

from .menu_tree_renderer import MenuTreeRenderer
from .main_gui import GUIClientWidget

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class QResourcesExporter(ResourcesExporter):
    """Exports resources in it's own thread. Has some signals for ui events."""

    def __init__(self, config: ExporterConfig = None) -> None:
        super().__init__(config)
        self.files_to_export_queue:typing.List[Path] = []

        self._export_thread = threading.Thread(target=self._export_thread_func)
        self._export_thread.daemon = True
        self._export_thread.start()
        self._mutex = threading.Lock()
        self._should_export_queue = False
        self._thread_should_close = False

        self.observe_print_status = False

    def __del__(self):
        self._mutex.acquire()
        self._thread_should_close = True
        self._mutex.release()
        self._export_thread.join()

        return super().__del__()

    def _export_thread_func(self):
        while True:
            self._mutex.acquire()
            if self._thread_should_close: break
            should_export = self._should_export_queue
            self._should_export_queue = False
            self._mutex.release()

            if should_export:
                self._thread_export_queued_resources()
            time.sleep(0.01)

    def export_queued_resources(self):
        self._mutex.acquire()
        self._should_export_queue = True
        self._mutex.release()

    def _thread_export_queued_resources(self):
        sorted_exts = self.resources_registry.sorted_extensions
        def sort_key(path:Path):
            ext = utils.normalize_extension(path.suffix)
            return sorted_exts.index(ext)
        files_to_export = sorted(self.files_to_export_queue, key=sort_key)
        for file in files_to_export:
            super().export_one_resource(file)
        self.files_to_export_queue.clear()

    def export_one_resource(self, filepath: Path):
        self.files_to_export_queue.append(filepath)