from logging import root
import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
from functools import partial

from .qt_exporter import QExportApiWidget, QResourcesExporter

from ..exporter import ResourcesExporter
from ..resources_registry import PluginMaker
from .. import utils

from .trees import *
from .export_pane import ExportPane

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

from .settings import storage

class GUIClientWidget(QExportApiWidget):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(res_exporter, *args, **kwargs)

        self.hlayout = QHBoxLayout()
        self.setLayout(self.hlayout)

        self.folders_view = FoldersView(self.res_exporter)
        self.files_view = FilesView(self.res_exporter)
        self.folders_view.on_dir_selected.connect(self.files_view.render_directory)

        self.export_pane = ExportPane(self.res_exporter)

        horizontal_layouts = [
            self.folders_view,
            self.files_view,
            self.export_pane
        ]
        
        self.splitters = []

        last_splitter = self.hlayout
        for i, widget in enumerate(horizontal_layouts):
            splitter = QSplitter(Qt.Orientation.Horizontal)
            self.splitters.append(splitter)
 
            splitter.addWidget(widget)
            
            last_splitter.addWidget(splitter)

            skey = f"h_splitter_{i}_state"
            def on_splitter_resize(splitter, skey):
                storage._settings.setValue(skey, splitter.saveState())
            splitter.splitterMoved.connect(partial(on_splitter_resize, splitter, skey))
            last_splitter = splitter
            
        for i, splitter in enumerate(self.splitters):
            skey = f"h_splitter_{i}_state"
            if storage._settings.contains(skey):
                splitter.restoreState(storage._settings.value(skey))

class MakePluginWindow(QDialog):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.res_exporter = res_exporter
        self.plugin_maker = PluginMaker("new_plugin")

        self.setWindowTitle("Create New Plugin")
        self.setWhatsThis(self.windowTitle())
        
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(QLabel("Plugin ID"))
        self.plugin_id_input = QLineEdit()
        self.plugin_id_input.setPlaceholderText(self.plugin_maker.id)
        self.vbox.addWidget(self.plugin_id_input)
        self.render_additional_templates(self.vbox)

        self.btn_box = QDialogButtonBox()
        self.vbox.addWidget(self.btn_box)
        self.btn_box.addButton("Create", QDialogButtonBox.ButtonRole.AcceptRole).pressed.connect(self.on_create_pressed)
        self.setLayout(self.vbox)

    def render_additional_templates(self, layout):
        for template_id in PluginMaker.ADDITIONAL_TEMPLATES:
            text = utils.snake_case_to_title(template_id)
            checkbox = QCheckBox(text)
            def state_change(id:str, state:int):
                setattr(self.plugin_maker, id, bool(state))
            checkbox.stateChanged.connect(partial(state_change, template_id))
            layout.addWidget(checkbox)

    def make_plugin(self):
        plugin_id = self.plugin_id_input
        try:
            self.plugin_maker.make_plugin()
            button = QMessageBox.question(self, 
                "Open plugin folder?", 
                f"Plugin successfully created on path \"{self.plugin_maker.directory}\"\nOpen plugin folder?")
            if button == QMessageBox.StandardButton.Yes:
                self.plugin_maker.edit_plugin()
            
            return True
        except Exception as e:
            QMessageBox.warning(self, str(e), str(e))
        return False

    def on_create_pressed(self):
        success = self.make_plugin()
        if success: self.close()