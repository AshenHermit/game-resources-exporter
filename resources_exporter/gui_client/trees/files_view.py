from ...exporter import ResourcesExporter, ResourcesRegistry
from .tree_view import *

class FilesView(TreeView):
    on_file_selected = pyqtSignal(Path)

    def __init__(self, res_exporter:ResourcesExporter, directory:Path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.res_exporter = res_exporter
        self.tree.setColumnCount(2)
        self.tree.headerItem().setText(0, "Name")
        self.tree.headerItem().setText(1, "Extension")
        self.tree.setSortingEnabled(True)

        directory = directory or CFD
        self.__directory:Path = directory
        self.directory = directory
        
        self.__extensions_filter:typing.List[Path] = None

    
    @property
    def extension_filter(self):
        return self.res_exporter.resources_registry.sorted_extensions   
    @extension_filter.setter
    def extension_filter(self, value:str):
        self.__extensions_filter = value

    @property
    def directory(self): return self.__directory
    @directory.setter
    def directory(self, value:Path):
        if self.__directory == value: return
        self.__directory = value
        self.render_files()

    def render_directory(self, dir:Path):
        self.directory = dir

    def clear_files(self):
        self.tree.clear()

    def render_files(self):
        self.clear_files()
        title = utils.cut_path(self.directory, 32).as_posix()
        self.title = title
        
        for file in self.__directory.glob("*"):
            ext = utils.normalize_extension(file.suffix)
            if self.extension_filter is not None:
                if utils.normalize_extension(file.suffix) not in self.extension_filter:
                    continue
            if file.is_dir(): continue

            file_item = PathTreeItem(file, self.tree, [file.name, ext])

    def on_custom_menu(self, pos:QPoint):
        cmenu = QMenu(self.tree)
        mr = MenuTreeRenderer(cmenu, self.tree)
        export_act = mr.add_action("Export")
        action = cmenu.exec(self.tree.mapToGlobal(pos))

        if action == export_act:
            for item in self.selected_items:
                self.res_exporter.export_one_resource(item.path)
