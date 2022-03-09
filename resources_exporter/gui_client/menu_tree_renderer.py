from functools import partial
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

class CustomQMenu(QMenu):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        CustomQMenu.make_menu_able_to_show_tooltip(self)

    @staticmethod
    def handle_menu_hovered(menu:QMenu, action:QAction):
        pos = QtGui.QCursor.pos()
        def show_tooltip():
            if QtGui.QCursor.pos() != pos: return
            QToolTip.showText(
                QtGui.QCursor.pos(), action.toolTip(),
                menu, menu.actionGeometry(action))
        QTimer.singleShot(500, show_tooltip)

    @staticmethod
    def make_menu_able_to_show_tooltip(menu:QMenu):
        menu.hovered.connect(partial(CustomQMenu.handle_menu_hovered, menu))


class MenuTreeRenderer():
    def __init__(self, menu_root: QMenu, parent: QWidget=None) -> None:
        self.menu_root:QMenu = menu_root
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
        
        menu_path = "/".join(nodes[:-1])
        menu = self.get_menu(menu_path)
        action = QAction(nodes[-1], menu, **kwargs)
        self.get_menu(menu_path).addAction(action)

        return action

    def add_separator(self):
        self.menu_root.addSeparator()