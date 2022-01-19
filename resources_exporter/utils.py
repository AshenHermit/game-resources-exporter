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