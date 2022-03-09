from contextlib import contextmanager
from dataclasses import replace
from io import StringIO
import os
from pathlib import Path
import importlib
import inspect
import re
import sys
import traceback
import typing
import subprocess

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

class StdoutSplitter():
    def __init__(self) -> None:
        self.old_stdout=None
        self.stream = StringIO()
        self.stdout_read_indx = 0
        self.capture_stdout()

    def capture_stdout(self):
        self.old_stdout = sys.stdout
        sys.stdout = self.stream

    def release_stdout(self):
        sys.stdout = self.old_stdout

    def __del__(self):
        self.release_stdout()

    def process_caret_return(self):
        text = self.stream.getvalue()
        cr_pos = text.rfind("\r")
        if cr_pos==0: return
        if cr_pos==len(text)-1: return
        if text[cr_pos+1] == "\n": return
        nl_pos = text[:cr_pos].rfind("\n")
        if nl_pos==-1:
            text = text[cr_pos:].replace("\r","")
        else:
            text = text[:nl_pos]+"\n"+text[cr_pos:].replace("\r","")
            
        self.stream = StringIO(text)
        self.release_stdout()
        self.capture_stdout()

    def read(self):
        self.stream.seek(self.stdout_read_indx)
        text = self.stream.read()
        self.stdout_read_indx += len(text)
        self.old_stdout.write(text)
        return text

    def read_all(self):
        self.read()
        self.process_caret_return()
        return self.stream.getvalue()

    @staticmethod
    @contextmanager
    def context():
        splitter = StdoutSplitter()
        yield splitter
        del splitter

def find_classes_in_dir(directory:Path, base_class=object):
    directory = Path(directory)
    classes_set = set()
    classes = []
    for file in directory.glob("*.py"):
        module = file.relative_to(CFD.parent)\
            .with_suffix("").as_posix().replace("/", ".")
        module = module
        module = importlib.import_module(module)

        for var in module.__dict__.values():
            if not inspect.isclass(var): continue
            if base_class not in inspect.getmro(var): continue
            if var in classes_set: continue
            classes_set.add(var)
            classes.append(var)
    
    return classes

def remove_last_cmd_line():
    CURSOR_UP_ONE = '\033[F'
    ERASE_LINE = '\033[K'
    sys.stdout.write(CURSOR_UP_ONE)
    sys.stdout.write(ERASE_LINE)

def strfdelta(tdelta):
    d = {}
    d["days"] = days = tdelta.days
    d["hours"], rem = hours,_ = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = minutes, seconds = divmod(rem, 60)
    s = ""
    pr = False
    lst = [[days, "d"], [hours, "h"], [minutes, "m"], [seconds, "s"]]
    for item in lst:
        if item[0]>0 or pr: s+=f" {item[0]}{item[1]}"; pr=True
    return s.strip()

def make_dirs_to_file(filepath:Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)

def cut_path(path, max_size=5):
    if not path:
        return path

    parts = list(Path(path).parts)

    path = Path(parts[0])
    for part in parts[1:-1]:
        path /= part
        if len(str(path)) >= max_size:
            path /= '...'
            break
    if len(parts) > 1:
        path /= parts[-1]
    return path

def normalize_extension(ext:str):
    return ext.replace(".", "").lower()

def open_folder_in_explorer(dir:Path):
    os.startfile(str(dir)+"\\")

def reveal_in_explorer(file:Path):
    subprocess.Popen(f'explorer /select,"{file}"')

def snake_case_to_title(s:str):
    if not s: return
    if len(s) == 1: return s.upper()
    s = s.replace("_", " ")
    s = s.replace("-", " ")
    s = " ".join(map(lambda x: x[0].upper() + x[1:].lower(), s.split(" ")))
    return s

def camel_to_snake(s:str):
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower()

def code_name_to_title(s:str):
    snake = camel_to_snake(s)
    return snake_case_to_title(snake)