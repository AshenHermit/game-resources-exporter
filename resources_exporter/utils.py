from pathlib import Path
import importlib
import inspect

def find_classes_in_dir(directory:Path, base_class=object, package="resources_exporter"):
    directory = Path(directory)
    classes = set()

    for file in directory.glob("**/*.py"):
        module = file.relative_to(directory.parent)\
            .with_suffix("").as_posix().replace("/", ".")
        module = package+"."+module
        module = importlib.import_module(module)

        for var in module.__dict__.values():
            if inspect.isclass(var):
                if base_class in inspect.getmro(var):
                    classes.add(var)
    
    return list(classes)


def resolved_path(str:str):
    path = Path(str).resolve()
    return path
