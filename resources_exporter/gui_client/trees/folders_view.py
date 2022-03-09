from resources_exporter.resource_types.res_local_config import ResLocalConfig, ResLocalSettings
from ...exporter import ResourcesExporter
from .tree_view import *

class AddRule(QDialog):
    def __init__(self, res_exporter:QResourcesExporter, *args, **kwargs):
        super().__init__(*args, **kwargs)

class FoldersView(FileSystemTree):
    on_dir_selected = pyqtSignal(Path)

    def __init__(self, res_exporter: QResourcesExporter, root_dir:Path=None, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.res_exporter = res_exporter
        root_dir = root_dir or CFD
        self.__root_dir:Path = root_dir
        self.root_dir = root_dir

        self.tree.headerItem().setText(0, "Raw Files")

        self.res_exporter.file_selected.connect(self._on_global_file_selected)

    def _on_global_file_selected(self, file:Path):
        for item in self.iter_items():
            item.setSelected(False)
            if item.path.samefile(file.parent):
                item.setSelected(True)
                self.reveal_item_parents(item)

    def _on_item_selected(self, item, idx):
        super()._on_item_selected(item, idx)
        self.on_dir_selected.emit(item.path)

    @property
    def root_dir(self): return self.__root_dir
    @root_dir.setter
    def root_dir(self, value:Path):
        self.__root_dir = value
        self.render_items()

    def render_items(self):
        self.clear_items()
        # self.title = utils.cut_path(self.__root_dir, 32).as_posix()
        self.fill_widget_with_folders(self.__root_dir, self.tree)
        if self.last_selected_path is not None:
            self.last_selected_path

    def fill_widget_with_folders(self, scan_folder:Path, parent_widget:QWidget):
        folders = [f for f in scan_folder.iterdir() if f.is_dir()]
        for folder in folders:
            try:
                folder_item = PathTreeItem(folder, parent_widget, [folder.name])
                self.fill_widget_with_folders(folder, folder_item)
            except:
                pass

    def make_context_menu(self, cmenu:QMenu):
        mr = MenuTreeRenderer(cmenu)
        def export_act():
            for item in self.selected_items:
                for file in item.path.rglob("*.*"):
                    self.res_exporter.export_one_resource(file)
        
        mr.add_action("Export").triggered.connect(export_act)
        cmenu.addSeparator()
        self.add_path_item_actions_in_cmenu(cmenu)

        def edit_settings():
            if len(self.selected_items)>0:
                item = self.selected_items[0]
                cfg = ResLocalConfig.of_filepath(item.path)
                cfg.save()
                os.startfile(cfg._storage_file)
        if len(self.selected_items)==1:
            cmenu.addSeparator()
            mr.add_action("Edit Resources Settings").triggered.connect(edit_settings)

        return cmenu