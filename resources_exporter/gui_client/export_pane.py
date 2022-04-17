from io import StringIO
from re import S
import sys
from pathlib import Path
import time
import typing
import PyQt5
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui, QtSvg
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

from ansi2html import Ansi2HTMLConverter

from ..exporter import ExportResult, ResourcesExporter
from .status_tabs.console import ConsoleWidget
from .status_tabs.export_results import ExportResultsWidget
from .qt_exporter import QExportApiWidget, QResourcesExporter
from .. import utils

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class ObservingButton(QExportApiWidget):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(res_exporter, *args, **kwargs)

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.vbox)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.label = QLabel()
        self.vbox.addWidget(self.label)
        self.button = QPushButton()
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vbox.addWidget(self.button)
        self.update_text()
        self.button.pressed.connect(self._on_pressed)

        self.text_update_timer = QTimer(self)
        self.text_update_timer.timeout.connect(self.update_text)
        self.text_update_timer.start(1000)

    def update_text(self):
        if self.res_exporter.is_observing:
            self.button.setText("Stop Observing")
            et = self.res_exporter.observing_status_printer.elapsed_time_str()
            ct = self.res_exporter.observing_status_printer.current_time()
            self.label.setText(f"observing... {ct} {et}")
            self.label.setVisible(True)
        else:
            self.label.setVisible(False)
            self.label.setText("")
            self.button.setText("Start Observing")

    def _on_pressed(self):
        if self.res_exporter.is_observing:
            self.res_exporter.stop_observing()
        else:
            self.res_exporter.start_observing(False)
        
        self.update_text()

class ChangedResExportButton(QExportApiWidget):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(res_exporter, *args, **kwargs)

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.vbox)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.button = QPushButton("Export changed res")
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vbox.addWidget(self.button)
        self.button.pressed.connect(self._on_pressed)

    def _on_pressed(self):
        self.res_exporter.export_resources()

class ButtonsPanel(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)
        
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        # observing button
        self.observing_button = ObservingButton(self.res_exporter)
        self.vbox.addWidget(self.observing_button)
        # export button
        self.export_button = ChangedResExportButton(self.res_exporter)
        self.vbox.addWidget(self.export_button)

class ExportStatus(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.setObjectName("export_status")
        self.hbox = QGridLayout()
        self.hbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.hbox.setSpacing(4)
        self.hbox.setContentsMargins(8,0,8,0)
        self.setLayout(self.hbox)

        self.icon = QtSvg.QSvgWidget(str(CFD/"icons/Wedges-3s-32px.svg"))
        self.icon.setHidden(True)
        self.hbox.addWidget(self.icon, 0, 0)
        self.hbox.setColumnStretch(0, 0)
        
        self.label = QLabel()
        self.hbox.addWidget(self.label, 0, 1)
        self.hbox.setColumnStretch(1, 2)

        self._current_file = None
        self.current_file = None

        self.res_exporter.export_started.connect(self.on_started_exporting)
        self.res_exporter.exported.connect(self.on_exported)

    @property
    def current_file(self):
        return self._current_file
    @current_file.setter
    def current_file(self, path:Path):
        self._current_file = path
        text = ""
        s = self.label.fontMetrics().height()

        if path is not None:
            self.icon.setHidden(False)
            text = path.relative_to(self.res_exporter.config.raw_folder).as_posix()
        else:
            self.icon.setHidden(True)

        text = self.label.fontMetrics().elidedText(text, Qt.TextElideMode.ElideLeft, self.label.width())
        self.label.setText(text)
        self.icon.setFixedSize(QSize(s,s))

    def on_started_exporting(self, file:Path):
        self.current_file = file

    def on_exported(self, result: ExportResult):
        print(result.resource)
        if result.resource:
            if result.resource.filepath == self.current_file:
                self.current_file = None

class ExportPane(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.vbox)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.tabs = QTabWidget()
        self.vbox.addWidget(self.tabs)
        
        self.results_tab = ExportResultsWidget(self.res_exporter)
        self.tabs.addTab(self.results_tab, "Export Results")
        self.console_tab = ConsoleWidget(self.res_exporter)
        self.tabs.addTab(self.console_tab, "Log")

        self.export_status = ExportStatus(self.res_exporter)
        self.vbox.addWidget(self.export_status)

        self.buttons_panel = ButtonsPanel(self.res_exporter) 
        self.vbox.addWidget(self.buttons_panel)