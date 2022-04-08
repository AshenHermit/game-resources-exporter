from multiprocessing import Process
import subprocess
from functools import partial
from .window_base import *
import colorama

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

RUN_EXPORTER_ON_EXIT = False

class PathReference():
    def __init__(self, path:Path=None) -> None:
        self.path:Path = path or Path()
class InputPathWidget(QWidget):
    def __init__(self, path:Path=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._path_ref = PathReference(path)

        self.setObjectName("InputPathWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('QWidget#InputPathWidget{ background-color: rgba(255, 255, 255, .05); }\n'+\
        'QWidget{ background-color: rgba(255, 255, 255, .0); }')

        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)

        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.hbox.addWidget(self.path_label)
        self.button = QPushButton("...")
        self.button.pressed.connect(self.select_file)
        self.button.setMaximumWidth(32)
        self.hbox.addWidget(self.button)

        self.path = path

    @property
    def path(self)->Path:
        return self._path_ref.path
    @path.setter
    def path(self, path:Path):
        self._path_ref.path = path
        self.path_label.setText(path.as_posix())
    @property
    def path_ref(self):
        return self._path_ref

    def select_file(self):
        options = QFileDialog.Options()

        if self.path.exists():
            dir = str(self.path.resolve().parent)

        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Open", 
            dir, "Excel (*.xls *.xlsx)", 
            options=options)
        if filename:
            self.path = Path(filename)
    
class ProjectItem(QWidget):
    pressed = pyqtSignal()
    removed = pyqtSignal()
    def __init__(self, path:Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.path = path

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("project_item")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.vbox = QVBoxLayout()
        # self.vbox.setSpacing(0)
        # self.vbox.setContentsMargins(0,0,0,0)
        self.setLayout(self.vbox)

        self.title = QLabel(utils.code_name_to_title(path.name))
        self.title.setWordWrap(True)
        self.vbox.addWidget(self.title)
        self.title.setObjectName("project_item_title")

        self.minor = QLabel(path.as_posix())
        self.minor.setWordWrap(True)
        self.vbox.addWidget(self.minor)
        self.minor.setObjectName("project_item_minor")

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        menu = CustomQMenu()
        mr = MenuTreeRenderer(menu)
        def open_folder():
            utils.open_folder_in_explorer(self.path)
        mr.add_action("Open folder").triggered.connect(open_folder)

        menu.addSeparator()

        def remove():
            storage.remove_project(self.path)
            self.removed.emit()
        mr.add_action("Remove").triggered.connect(remove)
        menu.exec_(self.mapToGlobal(a0.pos()))

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            self.pressed.emit()
        return super().mousePressEvent(a0)

class ProjectsList(QScrollArea):
    path_selected = pyqtSignal(Path)
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll_widget.setObjectName("projects_list")

        self.scroll_vbox = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_vbox)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)

        self.render_items()

    def render_items(self):
        for i in reversed(range(self.scroll_vbox.count())):
            item = self.scroll_vbox.itemAt(i)
            if item.widget():
                self.scroll_vbox.itemAt(i).widget().setParent(None)
            else:
                self.scroll_vbox.removeItem(item)
        
        for project_dir in storage.get_projects_paths():
            item = ProjectItem(project_dir)
            def item_pressed(item: ProjectItem):
                self.path_selected.emit(item.path)
            item.pressed.connect(partial(item_pressed, item))
            item.removed.connect(self.render_items)
            self.scroll_vbox.addWidget(item)

        self.scroll_vbox.addStretch(1)

class ProjectMaker(CustomWindow):
    called_exporter = pyqtSignal(str)
    def init_ui(self):
        self.exit_on_project_open = False
        self.setWindowTitle('Res Exporter Projects List')

        self.vbox = QVBoxLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.vbox)
        self.setCentralWidget(self.main_widget)

        self.list_title = QLabel("Resources Exporter")
        self.list_title.setObjectName("big_title")
        self.vbox.addWidget(self.list_title)

        self.list_title = QLabel("Projects List")
        self.list_title.setObjectName("title")
        self.vbox.addWidget(self.list_title)

        self.projects_list = ProjectsList()
        self.vbox.addWidget(self.projects_list)
        self.projects_list.path_selected.connect(self.open_project)
        
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.open_button = QPushButton("Open Project Folder")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.setObjectName("title")
        self.open_button.pressed.connect(self.select_and_open_project)
        self.vbox.addWidget(self.open_button)

        centerPoint = QDesktopWidget().availableGeometry().center()
        if storage.proj_manager_win_size is None: storage.proj_manager_win_size = QSize(512, 512)
        if storage.proj_manager_win_pos is None:
            s = storage.proj_manager_win_size
            storage.proj_manager_win_pos = centerPoint - QPoint(s.width(), s.height())/2
        self.resize(storage.proj_manager_win_size)
        self.move(storage.proj_manager_win_pos)

    def select_and_open_project(self):
        paths = storage.get_projects_paths(str)
        if len(paths)>0: last_dir = paths[0]
        else: last_dir = ""
        foldername = QFileDialog.getExistingDirectory(
            self, "Open Project Folder", last_dir)
        if foldername:
            dir = Path(foldername)
            self.open_project(dir)

    def open_project(self, dir:Path):
        global RUN_EXPORTER_ON_EXIT
        RUN_EXPORTER_ON_EXIT = True
        self.called_exporter.emit(str(dir))
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        storage.proj_manager_win_size = self.size()
        storage.proj_manager_win_pos = self.pos()
        
        super().closeEvent(a0)

def main():
    colorama.init()
    app = QApplication(sys.argv)

    win = ProjectMaker()
    win.exit_on_project_open = True
    win.show()

    app.exec_()

if __name__ == '__main__':
    main()
