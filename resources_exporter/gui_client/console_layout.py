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

from ..exporter import ResourcesExporter
from .. import utils
from termcolor import colored
from threading import Thread

class ObservingButton(QVBoxLayout):
    def __init__(self, res_exporter:ResourcesExporter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.res_exporter = res_exporter

        self.label = QLabel()
        self.addWidget(self.label)
        self.button = QPushButton()
        self.addWidget(self.button)
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
            self.res_exporter.start_observing()
        
        self.update_text()

class StdoutSplitter():
    def __init__(self) -> None:
        self.old_stdout=None
        self.stream = StringIO()
        self.stdout_read_indx = 0
        self.capture_stdout()

    def capture_stdout(self):
        self.old_stdout = sys.stdout
        sys.stdout = self.stream

    def release_stdout(self):
        sys.stdout = self.old_stdout

    def __del__(self):
        self.release_stdout()

    def process_caret_return(self):
        text = self.stream.getvalue()
        cr_pos = text.rfind("\r")
        if cr_pos==0: return
        if cr_pos==len(text)-1: return
        if text[cr_pos+1] == "\n": return
        nl_pos = text[:cr_pos].rfind("\n")
        if nl_pos==-1:
            text = text[cr_pos:].replace("\r","")
        else:
            text = text[:nl_pos]+"\n"+text[cr_pos:].replace("\r","")
            
        self.stream = StringIO(text)
        self.release_stdout()
        self.capture_stdout()

    def read(self):
        self.stream.seek(self.stdout_read_indx)
        text = self.stream.read()
        self.stdout_read_indx += len(text)
        self.old_stdout.write(text)
        return text

    def read_all(self):
        self.read()
        self.process_caret_return()
        return self.stream.getvalue()
        

class ConsoleLayout(QVBoxLayout):
    on_dir_selected = pyqtSignal(Path)

    def __init__(self, res_exporter:ResourcesExporter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.res_exporter = res_exporter

        self.text_edit = QTextEdit()
        self.last_text = ""
        # self.text_edit.setLineWrapColumnOrWidth(6000)
        # self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.addWidget(self.text_edit)
        self.text_edit.setReadOnly(True)
        self.text_cursor = QTextCursor(self.text_edit.document())
        self.ansi2html_converter = Ansi2HTMLConverter(inline=True)

        self.stdout = StdoutSplitter()

        self.observing_button = ObservingButton(self.res_exporter)
        self.addLayout(self.observing_button)

        self.print_timer = QTimer(self)
        self.print_timer.start(10)
        self.print_timer.timeout.connect(self._print_update)

    def _print_update(self):
        text = self.stdout.read()

        if text and text!=self.last_text:
            self.last_text = text
            html = self.ansi2html_converter.convert(text, full=False)
            html = html.replace("\n", "<br>")
            # self.text_edit.clear()
            self.text_cursor.insertHtml(html)
            # self.text_edit.setText(text)
            self.text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End, QtGui.QTextCursor.MoveMode.MoveAnchor)
        