import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os

from ..menu_tree_renderer import MenuTreeRenderer
from ... import utils

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class TreeView(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__title_label = QLabel("")
        self.__tree = QTreeWidget()
        self.__tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        # self.addWidget(self.__title_label)
        self.addWidget(self.__tree)

        self.__tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__tree.customContextMenuRequested.connect(self.on_custom_menu)

    @property
    def tree(self):
        return self.__tree
    @property
    def title(self):
        return self.__title_label.text()
    @title.setter
    def title(self, value:str):
        value = str(value)
        self.__title_label.setText(value)

    @property
    def selected_items(self):
        return self.tree.selectedItems()

    def on_custom_menu(self, pos:QPoint):
        cmenu = QMenu(self.tree)
        mr = MenuTreeRenderer(cmenu, self.tree)
        action = cmenu.exec(self.tree.mapToGlobal(pos))

class PathTreeItem(QTreeWidgetItem):
    def __init__(self, path:Path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path