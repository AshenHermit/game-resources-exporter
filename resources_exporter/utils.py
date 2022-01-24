from pathlib import Path
import importlib
import inspect
import sys

def find_classes_in_dir(directory:Path, base_class=object, package="resources_exporter"):
    directory = Path(directory)
    classes = set()

    for file in directory.glob("*.py"):
        module = file.relative_to(directory.parent)\
            .with_suffix("").as_posix().replace("/", ".")
        module = package+"."+module
        module = importlib.import_module(module)

        for var in module.__dict__.values():
            if inspect.isclass(var):
                if base_class in inspect.getmro(var):
                    classes.add(var)
    
    return list(classes)

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