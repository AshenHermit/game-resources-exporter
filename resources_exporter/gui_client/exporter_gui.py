import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

import logging
import threading
import time

from ..exporter import ExporterConfig, ResourcesExporter
from .. import utils

from .menu_tree_renderer import MenuTreeRenderer
from .main_gui import GUIClientWidget
from .qt_exporter import QResourcesExporter

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

logger = logging.getLogger(__name__); logger.setLevel(logging.DEBUG)	#output DEBUG or higher level messages
handler = logging.StreamHandler(); handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(threadName)s - %(levelname)s: %(message)s'))
logger.addHandler(handler)

class GUIClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.res_exporter = QResourcesExporter()

        self._running_loop = False
        self._update_loop_timer = QTimer(self)
        self._update_loop_timer.timeout.connect(self.update)

        self.styles_filepath = CFD/"styles/dark/stylesheet.qss"
        
        self.init_ui()

    def setup_stylesheet(self):
        stylesheet = self.styles_filepath.read_text()
        styles_folder_path = (CFD/"styles").as_posix()
        stylesheet = stylesheet.replace("url(:", f"url({styles_folder_path}/")
        qApp.setStyleSheet(stylesheet)

    def init_ui(self):
        mr = MenuTreeRenderer(self.menuBar(), self)

        mr.add_action("File/Keke")
        mr.add_action("File/What/do smth").triggered.connect(self.do_smth)

        self.main_widget = GUIClientWidget(self.res_exporter)
        self.main_widget.folders_view.root_dir = self.res_exporter.config.raw_folder 

        self.setCentralWidget(self.main_widget)

        self.setup_stylesheet()

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Submenu')
        self.show()

    def contextMenuEvent(self, event):
        cmenu = QMenu(self)
        mr = MenuTreeRenderer(cmenu, self)

        newAct = mr.add_action("New")
        mr.add_action("Cool menu/Well well")
        openAct = mr.add_action("Open")
        quitAct = mr.add_action("Quit")
        action = cmenu.exec(self.mapToGlobal(event.pos()))

        if action == quitAct:
            qApp.quit()

    def do_smth(self):
        print("DOING")

    def update(self):
        self.res_exporter.export_queued_resources()
        if self.res_exporter.is_observing:
            self.res_exporter.update_observer()

    def start_update_loop(self):
        self._running_loop = True
        self._update_loop_timer.start(10)

    def stop_update_loop(self):
        self._running_loop= False
        self._update_loop_timer.stop()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.stop_update_loop()
        return super().closeEvent(a0)

def main():
    logger.debug("I'm main thread.")
    app = QApplication(sys.argv)

    ex = GUIClient()
    ex.start_update_loop()

    app.exec_()

if __name__ == '__main__':
    main()
