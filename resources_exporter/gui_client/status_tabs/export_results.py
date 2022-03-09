from functools import partial
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
from ..menu_tree_renderer import MenuTreeRenderer
from ..icon_manager import IconManager

from ansi2html import Ansi2HTMLConverter

from ...exporter import ExportResult, ResourcesExporter
from ..qt_exporter import QExportApiWidget, QResourcesExporter
from ... import utils
from termcolor import colored
from threading import Thread

class ExportResultWidget(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, export_result: ExportResult, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)
        self.export_result = export_result
        self.build()

    def build(self):
        pass

class ResultHeader(ExportResultWidget):
    pressed = pyqtSignal()
    def build(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("export_result_header")

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.header_box = QHBoxLayout()
        self.setLayout(self.header_box)

        self.color_rect = QWidget()
        self.header_box.addWidget(self.color_rect)
        self.color_rect.setMinimumWidth(3)
        self.color_rect.setMaximumWidth(3)
        if self.export_result.success:
            self.color_rect.setObjectName("success_export_result_color_rect")
        else:
            self.color_rect.setObjectName("fail_export_result_color_rect")

        self.info_box = QVBoxLayout()
        self.header_box.addLayout(self.info_box, 1)

        path = self.export_result.resource.filepath.relative_to(self.export_result.resource.config.raw_folder).as_posix()
        self.info_res_path = QLabel(path)
        self.info_res_path.setWordWrap(True)
        self.info_box.addWidget(self.info_res_path)
    
        res_type = utils.code_name_to_title(self.export_result.resource.__class__.__name__)
        self.info_res_type_label = QLabel(res_type)
        self.info_res_type_label.setWordWrap(True)
        self.info_box.addWidget(self.info_res_type_label)
        self.info_res_type_label.setObjectName("export_result_header_info_minor")
        
        self.info_right_box = QVBoxLayout()
        self.header_box.addLayout(self.info_right_box)
        self.icon = QLabel()
        self.icon.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.icon.setPixmap(IconManager.get_pixmap_by_path(self.export_result.resource.__class__.get_icon()))
        self.info_right_box.addWidget(self.icon)
        
        self.info_right_box.addStretch(1)

        self.info_date = QLabel(self.export_result.date.strftime("%H:%M"))
        self.info_date.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.info_date.setObjectName("export_result_info_date")
        self.info_right_box.addWidget(self.info_date)

    def contextMenuEvent(self, ev: QtGui.QContextMenuEvent) -> None:
        menu = QMenu()
        mr = MenuTreeRenderer(menu)

        def go_to_res():
            self.res_exporter.select_file(self.export_result.resource.filepath)
        mr.add_action("Go to resource").triggered.connect(go_to_res)
        
        def export_res():
            self.res_exporter.export_one_resource(self.export_result.resource.filepath)
        mr.add_action("Export").triggered.connect(export_res)
        
        menu.exec(self.mapToGlobal(ev.pos()))

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed.emit()
        return super().mousePressEvent(ev)

class ResultDetails(ExportResultWidget):
    def build(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("export_result_details")
        
        self.box = QVBoxLayout()
        self.setLayout(self.box)
        self.setMaximumHeight(230)
        self.box.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ansi2html_converter = Ansi2HTMLConverter(inline=True)
        text = self.export_result.out_log.strip()

        html = self.ansi2html_converter.convert(text, full=False)
        html = html.replace("\n", "<br>")
        # self.text_edit.clear()

        self.doc = QTextEdit()
        self.doc.setMouseTracking(False)
        self.doc.setReadOnly(True)
        self.doc.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.doc.setTextInteractionFlags(Qt.CursorShape.IBeamCursor)
        self.text_cursor = QTextCursor(self.doc.document())
        self.text_cursor.insertHtml(html)
        # self.doc.setSele(True)
        # self.doc.setCursor(Qt.CursorShape.IBeamCursor)
        # self.doc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.box.addWidget(self.doc)

        size = self.doc.document().size().toSize()
        self.doc.setFixedHeight( min(size.height(), 230-16) )

class ExportResultCard(ExportResultWidget):
    def build(self):
        self.setObjectName("export_result_card")

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.vbox)

        # header
        self.header = ResultHeader(self.res_exporter, self.export_result)
        self.header.pressed.connect(self.toggle_details)
        self.vbox.addWidget(self.header)

        # details
        self.details = ResultDetails(self.res_exporter, self.export_result)
        self.vbox.addWidget(self.details)
        self.details.setHidden(True)

    def toggle_details(self):
        self.details.setHidden(not self.details.isHidden())

class ExportResultsWidget(QExportApiWidget):
    def __init__(self, res_exporter: QResourcesExporter, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("export_results_panel")

        self.scroll_box = QVBoxLayout()
        self.scroll_box.setSpacing(0)
        self.scroll_box.setContentsMargins(1,1,1,1)
        self.setLayout(self.scroll_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_box.addWidget(self.scroll_area)

        self.scroll_widget = QWidget()
        self.vbox = QVBoxLayout()
        self.scroll_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll_widget.setObjectName("export_results_panel")

        self.vbox.setSpacing(2)
        self.vbox.setContentsMargins(1,1,1,1)

        self.scroll_widget.setLayout(self.vbox)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vbox.addStretch(1)

        self.res_exporter.exported.connect(self.on_export)

    def on_export(self, result:ExportResult):
        if result is None: return
        if result.resource is None: return
        
        result_widget = ExportResultCard(self.res_exporter, result)
        self.vbox.insertWidget(self.vbox.count()-1, result_widget)
        
        def scroll_to_bottom():
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setSliderPosition(self.scroll_box.geometry().height())
        # scroll_to_bottom()
        QTimer.singleShot(100, scroll_to_bottom)
        QTimer.singleShot(400, scroll_to_bottom)
        # QTimer.singleShot(100, scroll_to_bottom)
        # QTimer.singleShot(200, scroll_to_bottom)
        
        # self.scroll_area.ensureVisible(0, self.scroll_box.geometry().height(), 0, 0)

    def clear(self):
        for i in reversed(range(self.vbox.count())):
            item = self.vbox.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key.Key_L:
                self.clear()
        super().keyPressEvent(e)