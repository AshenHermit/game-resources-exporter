from io import StringIO
from re import S
import sys
from pathlib import Path
import time
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

from ansi2html import Ansi2HTMLConverter

from ...exporter import ResourcesExporter
from ..qt_exporter import QExportApiWidget, QResourcesExporter
from ... import utils
from termcolor import colored
from threading import Thread

class ConsoleWidget(QExportApiWidget):
    on_dir_selected = pyqtSignal(Path)

    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(res_exporter, *args, **kwargs)
        
        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(1,1,1,1)
        self.setLayout(self.vbox)

        self.text_edit = QTextEdit()
        self.last_text = ""
        # self.text_edit.setLineWrapColumnOrWidth(6000)
        # self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.vbox.addWidget(self.text_edit)
        self.text_edit.setReadOnly(True)
        self.text_cursor = QTextCursor(self.text_edit.document())
        self.ansi2html_converter = Ansi2HTMLConverter(inline=True)

        self.stdout = utils.StdoutSplitter()

        self.print_timer = QTimer(self)
        self.print_timer.start(10)
        self.print_timer.timeout.connect(self._print_update)

    def _print_update(self):
        text = self.stdout.read()

        if text:
            self.last_text = text
            html = self.ansi2html_converter.convert(text, full=False)
            html = html.replace("\n", "<br>")
            # self.text_edit.clear()
            self.text_cursor.insertHtml(html)
            # self.text_edit.setText(text)
            self.text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End, QtGui.QTextCursor.MoveMode.MoveAnchor)
        
    def clear(self):
        self.text_edit.clear()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key.Key_L:
                self.clear()
        super().keyPressEvent(e)