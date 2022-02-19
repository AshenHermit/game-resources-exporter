import os
from pathlib import Path
import importlib
import inspect
import sys
import traceback

CFD = Path(__file__).parent.resolve()
CWD = Path(os.getcwd()).resolve()

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