from logging import root
import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

from ..exporter import ResourcesExporter
from .. import utils

from .trees import *
from .console_layout import ConsoleLayout

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class GUIClientWidget(QWidget):
    def __init__(self, res_exporter:ResourcesExporter, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.res_exporter = res_exporter

        self.hlayout = QHBoxLayout()

        self.folders_view = FoldersView(self.res_exporter)
        self.files_view = FilesView(self.res_exporter)
        self.folders_view.on_dir_selected.connect(self.files_view.render_directory)
        self.console_view = ConsoleLayout(self.res_exporter)

        horizontal_layouts = [
            self.folders_view,
            self.files_view,
            self.console_view
        ]

        last_splitter = self.hlayout
        for i, lay in enumerate(horizontal_layouts):
            splitter = QSplitter(Qt.Orientation.Horizontal)
            w = QFrame()
            w.setLayout(lay)
            splitter.addWidget(w)
            
            last_splitter.addWidget(splitter)
            last_splitter = splitter

        self.setLayout(self.hlayout)