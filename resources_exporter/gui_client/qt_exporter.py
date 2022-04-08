from enum import Enum, auto

import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

import threading, queue
import time

from resources_exporter.resource_types.res_local_config import ResLocalConfig

from ..exporter import ExportResult, ExporterConfig, FileSystemCallbackEventHandler, ResourcesExporter
from .. import utils

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class QueueItem():
    class Type(Enum):
        NONE = auto()
        EXPORT_STARTED = auto()
        EXPORTED = auto()
        FILESYSTEM_CHANGED = auto()
    def __init__(self, type:Type=Type.NONE, data=None) -> None:
        self.type = type
        self.data = data

class QResourcesExporter(ResourcesExporter, QObject):
    """Exports resources in it's own thread. Has some signals for ui events."""
    exported = pyqtSignal(ExportResult)
    export_started = pyqtSignal(Path)
    file_system_changed = pyqtSignal()
    file_selected = pyqtSignal(Path)

    def __init__(self, config: ExporterConfig = None, project_dir:Path=None) -> None:
        QObject.__init__(self)
        super().__init__(config, project_dir)
        self.threaded_files_to_export_queue:typing.List[Path] = []
        self.observe_print_status = False
        self._should_export_queue = False
        self._thread_should_close = False
        self._mutex = threading.Lock()
        self._export_thread = threading.Thread(target=self._export_thread_func)
        self._export_thread.daemon = True
        self._export_thread.start()

        self.files_observer = Observer()
        self.start_file_system_change_observer()

        self._events_queue = queue.Queue()

        self.queues_check_timer = QTimer(self)
        self.queues_check_timer.timeout.connect(self.update_queues_check)
        self.queues_check_timer.start(10)

        self.old_cfg_verbose = self.config.verbose
        self.config.verbose = True

    def __del__(self):
        self.config.verbose = self.old_cfg_verbose
        with self._mutex:
            self._thread_should_close = True
        self._export_thread.join()
        self.files_observer.stop()
        self.files_observer.join()

        return super().__del__()

    def _export_thread_func(self):
        while True:
            with self._mutex:
                if self._thread_should_close: break
                should_export = self._should_export_queue
                self._should_export_queue = False

            if should_export:
                self._thread_export_queued_resources()
            time.sleep(0.01)

    def export_queued_resources(self):
        with self._mutex:
            self._should_export_queue = True

    def _thread_export_queued_resources(self):
        sorted_exts = self.resources_registry.sorted_extensions
        def sort_key(path:Path):
            ext = utils.normalize_extension(path.suffix)
            idx = -1
            try:
                idx = sorted_exts.index(ext)
            except:
                pass
            return idx
        
        with self._mutex:
            files_to_export = sorted(list(self.threaded_files_to_export_queue), key=sort_key)
            self.threaded_files_to_export_queue.clear()
        
        for file in files_to_export:
            self._events_queue.put(QueueItem(QueueItem.Type.EXPORT_STARTED, file))
            result = super().export_one_resource(file)
            self._events_queue.put(QueueItem(QueueItem.Type.EXPORTED, result))

    def export_one_resource(self, filepath: Path):
        with self._mutex:
            self.threaded_files_to_export_queue.append(filepath)
            ResLocalConfig.clear_cache()
    
    def update_queues_check(self):
        while not self._events_queue.empty():
            qitem = self._events_queue.get()

            if qitem.type is QueueItem.Type.EXPORT_STARTED:
                self.export_started.emit(qitem.data)

            elif qitem.type is QueueItem.Type.EXPORTED:
                result = qitem.data
                self.exported.emit(result)
                self.files_iterator.update_file_info(result.resource.filepath)

            elif qitem.type is QueueItem.Type.FILESYSTEM_CHANGED:
                self.file_system_changed.emit()

    def _on_file_system_change(self):
        self._events_queue.put(QueueItem(QueueItem.Type.FILESYSTEM_CHANGED))

    def start_file_system_change_observer(self):
        self.files_observer = Observer()
        def _fs_obj_change(path:str):
            if Path(path).name!=ResLocalConfig._CONFIG_FILENAME:
                self._on_file_system_change()
        event_handler = FileSystemCallbackEventHandler(_fs_obj_change)
        self.files_observer.schedule(event_handler, str(self.config.raw_folder), recursive=True)
        self.files_observer.start()

    def select_file(self, file:Path):
        self.file_selected.emit(file)

class QExportApiWidget(QWidget):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.res_exporter = res_exporter