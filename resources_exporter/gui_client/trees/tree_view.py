import sys
from pathlib import Path
import typing
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import * 
import os
import pyperclip

from send2trash import send2trash

from ..menu_tree_renderer import CustomQMenu, MenuTreeRenderer
from ... import utils

from ..qt_exporter import QExportApiWidget, QResourcesExporter

from functools import partial
from ..settings import storage

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class TreeView(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.__title_label = QLabel("")
        self.__title_label.setWordWrap(True)
        self.__tree = QTreeWidget()
        self.__tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.vbox.addWidget(self.__tree)

        self.__tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__tree.customContextMenuRequested.connect(self._on_custom_menu)
        qApp.aboutToQuit.connect(self.save_settings)

        self.setup_storage()

    def setup_storage(self):
        header = self.tree.header()
        skey = f"{self.__class__}_header_state"
        if storage._settings.contains(skey):
            header.restoreState(storage._settings.value(skey))

    def save_settings(self):
        skey = f"{self.__class__}_header_state"
        storage._settings.setValue(skey, self.tree.header().saveState())

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

    def iter_items(self, root=None):
        def recurse(parent):
            for ch in range(parent.childCount()):
                child = parent.child(ch)
                yield child
                if child.childCount()>0:
                    yield from recurse(child)
        if root is not None:
            yield from recurse(root)
        else:
            yield from recurse(self.tree.invisibleRootItem())

    def _on_custom_menu(self, pos:QPoint):
        cmenu = CustomQMenu(self.tree)
        self.make_context_menu(cmenu)
        cmenu.exec(self.tree.viewport().mapToGlobal(pos))

    def make_context_menu(self, cmenu:QMenu):
        return cmenu

class FileSystemTree(TreeView):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.search_input = QLineEdit()
        self.search_input.setHidden(True)
        self.search_input.textChanged.connect(self.on_search_text_change)
        self.vbox.insertWidget(0, self.search_input)

        self.res_exporter.file_system_changed.connect(self.refresh_tree)
        self.last_selected_path = None
        self.tree.itemClicked.connect(self._on_item_selected)

    def _on_item_selected(self, item, idx):
        self.last_selected_path = item.path

    @property
    def is_searching(self):
        return not self.search_input.isHidden()

    def add_path_item_actions_in_cmenu(self, cmenu:QMenu):
        mr = MenuTreeRenderer(cmenu)

        def reveal_in_explorer():
            for item in self.selected_items:
                utils.reveal_in_explorer(item.path)
        mr.add_action("Reveal in explorer").triggered.connect(reveal_in_explorer)

        def copy_paths():
            paths = map(lambda item: item.path.as_posix(), self.selected_items)
            paths = "; ".join(paths)
            if paths.strip()!="":
                pyperclip.copy(paths)
        mr.add_action("Copy path").triggered.connect(copy_paths)

    def clear_items(self):
        self.tree.clear()

    def render_items(self):
        self.clear_items()

    def refresh_tree(self):
        self.render_items()
        if self.is_searching:
            self.reveal_search_results()
        else:
            self.reveal_all_items()

    def delete_selected_items(self):
        for item in self.selected_items:
            if not item.path.exists(): continue
            send2trash(str(item.path))

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key.Key_F:
                self.on_search_action()

        if e.key() == Qt.Key.Key_Escape:
            self.search_input.setHidden(True)
            self.reveal_all_items()

        if e.key() == Qt.Key.Key_Delete and self.tree.hasFocus():
            self.delete_selected_items()
        
        super().keyPressEvent(e)
    
    def on_search_action(self) -> None:
        if not self.tree.hasFocus(): return
        self.search_input.setHidden(False)
        self.search_input.setFocus()
        self.on_search_text_change()

    def on_search_text_change(self):
        self.reveal_search_results()

    def reveal_all_items(self):
        for item in self.iter_items():
            item.setHidden(False)
            if item.childCount()>0:
                item.setExpanded(False)
            if self.last_selected_path is not None:
                if str(item.path) == str(self.last_selected_path):
                    self.reveal_item_parents(item)
            
    def reveal_item_parents(self, item:QTreeWidgetItem):
        parent = item.parent()
        if parent is None: return
        parent.setExpanded(True)
        parent.setHidden(False)
        self.reveal_item_parents(parent)

    def show_item_children(self, item:QTreeWidgetItem):
        for i in range(item.childCount()):
            child = item.child(i)
            if child is None: continue
            child.setHidden(False)
            self.show_item_children(child)
    
    def reveal_search_results(self):
        search_string = self.search_input.text()

        for item in self.iter_items():
            item.setHidden(True)
            item.setExpanded(False)

        items = self.tree.findItems(search_string, Qt.MatchFlag.MatchRecursive | Qt.MatchFlag.MatchContains, 0)
        for item in items:
            item.setHidden(False)
            self.reveal_item_parents(item)
            self.show_item_children(item)

class PathTreeItem(QTreeWidgetItem):
    def __init__(self, path:Path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path