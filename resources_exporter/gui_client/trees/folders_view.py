from ...exporter import ResourcesExporter
from .tree_view import *

class FoldersView(TreeView):
    on_dir_selected = pyqtSignal(Path)

    def __init__(self, res_exporter:ResourcesExporter, root_dir:Path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        root_dir = root_dir or CFD
        self.__root_dir:Path = root_dir
        self.root_dir = root_dir

        self.tree.headerItem().setText(0, "Raw Files")
        
        self.tree.itemClicked.connect(self._on_dir_selected)

    def _on_dir_selected(self, item, idx):
        self.on_dir_selected.emit(item.path)

    @property
    def root_dir(self): return self.__root_dir
    @root_dir.setter
    def root_dir(self, value:Path):
        self.__root_dir = value
        self.render_folders()

    def clear_folders(self):
        self.tree.clear()

    def render_folders(self):
        self.clear_folders()
        self.title = utils.cut_path(self.__root_dir, 32).as_posix()
        self.fill_widget_with_folders(self.__root_dir, self.tree)

    def fill_widget_with_folders(self, scan_folder:Path, parent_widget:QWidget):
        folders = [f for f in scan_folder.iterdir() if f.is_dir()]
        for folder in folders:
            folder_item = PathTreeItem(folder, parent_widget, [folder.name])
            self.fill_widget_with_folders(folder, folder_item)