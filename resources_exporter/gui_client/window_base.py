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

from .menu_tree_renderer import CustomQMenu, MenuTreeRenderer
from .main_gui import GUIClientWidget, MakePluginWindow
from .qt_exporter import QResourcesExporter

from .settings import storage
from .icon_manager import IconManager

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.styles_filepath = CFD/"styles/dark/stylesheet.qss"
        self.setup_stylesheet()
        self.setWindowIcon(IconManager.get_icon_by_path(CFD/"icons/icon.png"))
        self.init_ui()

    def setup_stylesheet(self):
        stylesheet = self.styles_filepath.read_text()
        styles_folder_path = (CFD/"styles").as_posix()
        stylesheet = stylesheet.replace("url(:", f"url({styles_folder_path}/")
        qApp.setStyleSheet(stylesheet)
    
    def init_ui(self):
        pass