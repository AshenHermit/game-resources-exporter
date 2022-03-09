from functools import cache
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

class IconManager():
    
    @staticmethod
    @cache
    def get_icon_by_path(icon_path:Path):
        icon_path = icon_path.resolve()
        return QIcon(str(icon_path))

    @staticmethod
    @cache
    def get_pixmap_by_path(icon_path:Path, qsize = None):
        qsize = qsize or QSize(16, 16)
        icon = IconManager.get_icon_by_path(icon_path)
        return icon.pixmap(qsize)