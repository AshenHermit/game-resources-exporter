from cProfile import run
from ...resource_types import *
from ...exporter import ResourcesExporter, ResourcesRegistry
from .tree_view import *
from ..icon_manager import IconManager

class FilesView(FileSystemTree):
    on_file_selected = pyqtSignal(Path)

    def __init__(self, res_exporter: QResourcesExporter, directory:Path=None, *args, **kwargs) -> None:
        super().__init__(res_exporter, *args, **kwargs)

        self.tree.setColumnCount(2)
        self.tree.headerItem().setText(0, "Name")
        self.tree.headerItem().setText(1, "Extension")
        self.tree.setSortingEnabled(True)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        directory = directory or CFD
        self.__directory:Path = directory
        self.directory = directory
        
        self.__extensions_filter:typing.List[Path] = None

        self.icons_map = {}

        self.res_exporter.file_selected.connect(self._on_global_file_selected)

    def _on_global_file_selected(self, file:Path):
        self.directory = file.parent
        for item in self.iter_items():
            if item.path.samefile(file):
                item.setSelected(True)
    
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
        self.render_items()

    def render_directory(self, dir:Path):
        self.directory = dir

    def get_icon_by_path(self, icon_path:Path):
        return IconManager.get_icon_by_path(icon_path)

    def render_items(self):
        self.clear_items()
        title = utils.cut_path(self.directory, 32).as_posix()
        self.title = title
        
        for file in self.__directory.glob("*"):
            ext = utils.normalize_extension(file.suffix)
            if self.extension_filter is not None:
                if utils.normalize_extension(file.suffix) not in self.extension_filter:
                    continue
            if file.is_dir(): continue

            file_item = PathTreeItem(file, self.tree, [file.name, ext])
            res_class = self.res_exporter.resources_registry.get_res_class_by_filepath(file)
            if res_class is not None:
                icon_path = res_class.get_icon()
                if icon_path is not None:
                    for i in range(2):
                        file_item.setIcon(i, self.get_icon_by_path(icon_path))

    def make_context_menu(self, cmenu:QMenu):
        cmenu.setToolTipsVisible(True)
        mr = MenuTreeRenderer(cmenu)
        def export_act():
            for item in self.selected_items:
                self.res_exporter.export_one_resource(item.path)
        mr.add_action("Export").triggered.connect(export_act)

        cmenu.addSeparator()
        self.add_path_item_actions_in_cmenu(cmenu)
        cmenu.addSeparator()
        # cmenu.addSection("Commands")
        self.render_cmds(mr)
        cmenu.addSeparator()
        # cmenu.addSection("Export settings")
        self.render_settings(mr)

        return cmenu

    def render_cmds(self, mr:MenuTreeRenderer):
        paths = list(map(lambda x: x.path, self.selected_items))
        res_classes = list(map(
            lambda x: self.res_exporter.resources_registry.get_res_class_by_filepath(x), paths))
        commands = Resource.get_commands_of_classes(*res_classes)

        def run_cmd(cmd, paths):
            for path in paths:
                self.res_exporter.run_resource_command(path, cmd.id)
        
        for cmd in commands:
            if not cmd.name: continue
            act = mr.add_action(f"{cmd.name}")
            act.setToolTip(cmd.description)
            act.triggered.connect(
                partial(run_cmd, cmd, paths)
            )

    def render_settings(self, mr:MenuTreeRenderer):
        paths = list(map(lambda x: x.path, self.selected_items))
        res_classes = list(map(
            lambda x: self.res_exporter.resources_registry.get_res_class_by_filepath(x), paths))
        settings = Resource.get_settings_of_classes(*res_classes)
        if len(paths)==0: return

        cfg = ResLocalConfig.of_filepath(paths[0])
        first_settings = cfg.get_settings_for_file(paths[0])
        def toggle_setting(paths:Path, setting_id:str):
            firstvalue = bool(getattr(first_settings, setting_id, False))
            for path in paths:
                try:
                    settings = cfg.get_settings_for_rule(path.name)
                    value = not firstvalue
                    setattr(settings, setting_id, value)
                except:
                    print(f"failed to set \"{setting_id}\" for file \"{path}\"")
            cfg.save()
        
        for cmd in settings:
            if not cmd.name: continue
            act = mr.add_action(f"{cmd.name} : {cmd.id}")
            act.setToolTip(cmd.description)
            act.setCheckable(True)
            act.setChecked(getattr(first_settings, cmd.id, False))
            act.triggered.connect(
                partial(toggle_setting, paths, cmd.id)
            )
        ResLocalConfig.clear_cache()
        
    def on_item_double_clicked(self, item: PathTreeItem, column: int) -> None:
        os.startfile(item.path)
