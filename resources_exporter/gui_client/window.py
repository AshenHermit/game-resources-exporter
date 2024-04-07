import argparse
import gc
import shlex
import subprocess
import traceback
from .window_base import *
from .project_maker import ProjectMaker
from .icon_manager import IconManager
import colorama

from termcolor import colored

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

CALLINIT = False
def run_new_exporter(cwd):
    cwd = str(cwd)
    exec = Path(sys.executable)
    args = [str(exec), str((CFD/"../../exporter.py").resolve()), "--init"]
    cmd = " ".join(map(lambda x: f'"{x}"', args))
    subprocess.Popen(f'start /b "" ' + cmd, 
        cwd=cwd, shell=True, close_fds=True, 
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
def run_res_exporter(cwd):
    try:
        ex = GUIClient(cwd)
        ex.res_exporter.init_workspace(False)
        ex.show()
        ex.start_update_loop()
    except:
        traceback.print_exc()
        print(colored("cant start exporter window, check project export config on path mistakes or something", "red"))
        utils.open_folder_in_explorer(cwd)

PROJECT_MANAGER = None

def run_project_maker():
    global PROJECT_MANAGER
    pm = ProjectMaker()
    def on_call_exporter(cwd):
        global CALLINIT
        CALLINIT = True
        run_res_exporter(cwd)

    pm.called_exporter.connect(on_call_exporter)
    pm.show()
    PROJECT_MANAGER = pm

class GUIClient(CustomWindow):
    def __init__(self, project_dir:Path=None):
        self.res_exporter = QResourcesExporter(project_dir=project_dir)
        storage.use_project(self.res_exporter.project_dir)
        super().__init__()

        self._running_loop = False
        self._update_loop_timer = QTimer(self)
        self._update_loop_timeout = 10
        self._update_loop_timer.timeout.connect(self.update)

    def init_ui(self):
        menu_bar = self.menuBar()
        CustomQMenu.make_menu_able_to_show_tooltip(menu_bar)
        mr = MenuTreeRenderer(menu_bar, self)

        file_menu = mr.get_menu("File")
        def eidt_config():
            os.startfile(str(self.res_exporter.config._storage_file))
        mr.add_action("File/Edit Exporter Config").triggered.connect(eidt_config)

        def open_proj_dir():
            utils.open_folder_in_explorer(self.res_exporter.project_dir)
        mr.add_action("File/Open Project Folder").triggered.connect(open_proj_dir)

        file_menu.addSeparator()
        def go_to_projects_list():
            run_project_maker()
            # self.close()
        mr.add_action("File/Go to Projects List").triggered.connect(go_to_projects_list)

        file_menu.addSeparator()
        
        def restart_exporter():
            run_res_exporter(self.res_exporter.project_dir)
            self.close()
        act = mr.add_action("File/Restart")
        act.triggered.connect(restart_exporter)

        mr.add_action("File/Quit").triggered.connect(qApp.quit)
        
        # plugins
        
        def make_new_plugin():
            MakePluginWindow(self.res_exporter).exec()
        mr.add_action("Plugins/Create New Plugin").triggered.connect(make_new_plugin)
        mr.get_menu("Plugins").addSeparator()

        for plugin in self.res_exporter.resources_registry.plugins:
            mr.get_menu(f"Plugins/{plugin.name}")
            for cmd in plugin.commands:
                act = mr.add_action(f"Plugins/{plugin.name}/{cmd.name}")
                act.setToolTip(cmd.description)
                act.triggered.connect(cmd.func)

        self.main_widget = GUIClientWidget(self.res_exporter)
        self.main_widget.folders_view.root_dir = self.res_exporter.config.raw_folder 

        self.setCentralWidget(self.main_widget)

        centerPoint = QDesktopWidget().availableGeometry().center()
        if storage.window_size is None: storage.window_size = QSize(1357, 608)
        if storage.window_pos is None:
            s = storage.window_size
            storage.window_pos = centerPoint - QPoint(s.width(), s.height())/2
        self.resize(storage.window_size)
        self.move(storage.window_pos)

        self.setWindowTitle('Resources Exporter - '+utils.code_name_to_title(self.res_exporter.project_dir.name))

    def do_smth(self):
        print("DOING")

    def update(self):
        self.res_exporter.export_queued_resources()
        if self.res_exporter.is_observing:
            self.res_exporter.update_observer()
        self.res_exporter.update_queues_check()

    def start_update_loop(self):
        self._running_loop = True
        self._update_loop_timer.start(self._update_loop_timeout)

    def stop_update_loop(self):
        self._running_loop= False
        self._update_loop_timer.stop()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.stop_update_loop()

        storage.window_size = self.size()
        storage.window_pos = self.pos()
        
        return super().closeEvent(a0)

def run_app():
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action='store_true', default=False)
    args = parser.parse_args()

    if (not ResourcesExporter.get_config_path(CWD).exists()) and not args.init:
        run_project_maker()
    else:
        run_res_exporter(CWD)

    app.exec()

def main():
    colorama.init()
    try:
        run_app()
    except:
        traceback.print_exc()
        a = input()

if __name__ == '__main__':
    main()
