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

class MenuTreeRenderer():
    def __init__(self, menu_root: QMenuBar, parent: QWidget) -> None:
        self.menu_root:QMenuBar = menu_root
        self.parent = parent
        self.menus = {}

    def get_menu(self, path:str):
        if path.strip()=="": return self.menu_root
        nodes = path.split("/")

        key = path
        if key not in self.menus:
            menu = QMenu(nodes[-1], self.parent)
            parent_menu_path = "/".join(nodes[:-1])
            self.get_menu(parent_menu_path).addMenu(menu)
            self.menus[key] = menu
        return self.menus[key]

    def add_action(self, path:str, **kwargs) -> QAction:
        """ path nodes are separated by / slash """
        if path.strip()=="": return None

        nodes = path.split("/")
        
        action = QAction(nodes[-1], self.parent, **kwargs)
        menu_path = "/".join(nodes[:-1])
        self.get_menu(menu_path).addAction(action)

        return action