from pathlib import Path
import typing
import os
import datetime

class TextRenderer():
    def __init__(self) -> None:
        self.text = ""
        self._indent:int = 0
    @property
    def indent(self): return self._indent
    @indent.setter
    def indent(self, value:int): self._indent = value

    def writeln(self, line:str=""):
        indent_str = "\t"*self.indent
        line = indent_str + line
        line += "\n"
        self.text += line
    def render(self) -> str:
        return ""

class ValveResRenderer(TextRenderer):
    def _wln(self, line:str=""):
        if line=="}": self.indent -= 1
        super().writeln(line)
        if line=="{": self.indent += 1

class QCFileMaker(ValveResRenderer):
    class CollisionModel(ValveResRenderer):
        def __init__(self) -> None:
            super().__init__()
            self.mass = -1
            self.concave = False
            self.phy_smd = "model_phy.smd"
            self.surfaceprop = "plastic"
        
        def render(self):
            self._wln(f'$surfaceprop "{self.surfaceprop}"')
            self._wln(f'$collisionmodel "{self.phy_smd}"')
            self._wln('{')

            if self.mass == -1: self._wln(f'$automass')
            else:               self._wln(f'$mass {self.mass}')

            if self.concave: self._wln(f'$concave')

            self._wln('}')
            self._wln('')
            return self.text
    
    class PropRenderer(ValveResRenderer):
        def __init__(self) -> None:
            super().__init__()
            self.base = "Plastic.Small"

        def render(self):
            self._wln(f'$keyvalues')
            self._wln('{')
            self._wln('prop_data')
            self._wln('{')
            self._wln(f"base {self.base}")
            self._wln('}')
            self._wln('}')
            self._wln()
            return self.text

    def __init__(self, filepath:Path=None) -> None:
        super().__init__()
        self.filepath: Path = filepath

        self.modelname = "model"
        self.cdmaterials = "models/id/model"
        self.body_name = "body"
        self.body_smd = "model_ref.smd"
        self.idle_sequence_smd = "model_ref.smd"

        self.collisionmodel:QCFileMaker.CollisionModel = None
        self.prop_data_renderer:QCFileMaker.PropRenderer = None

    def render(self):
        qc = ""
        self._wln(f'$modelname "{self.modelname}"')
        self._wln(f'$cdmaterials "{self.cdmaterials}"')
        self._wln(f'$body {self.body_name} "{self.body_smd}"')
        self._wln(f'$sequence idle "{self.idle_sequence_smd}"')
        self._wln()

        other_renderers = [self.collisionmodel, self.prop_data_renderer]
        for renderer in other_renderers:
            if renderer is not None:
                self._wln(renderer.render())
        
        return self.text

    def write(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(self.render())

    def update_file_mtime(self):
        now = now = datetime.datetime.now().timestamp()
        os.utime(self.filepath, (now, now))