# VTFEdit vmt renderer - https://github.com/NeilJed/VTFLib/blob/master/VTFEdit/VMTCreate.h

from pathlib import Path
import json

class VMTRenderer():
    def __init__(self, filepath:Path) -> None:
        self.filepath = filepath
        self._properties = {}
        self.shader = "VertexLitGeneric"
    
    # [[[cog
    # import sys
    # sys.path.append("../../../libs/")
    # import cog, handyxml
    # for cmd in handyxml.xpath('vmt_renderer_fields.xml', 'command'):
    #     cog.outl(f"@property")
    #     cog.outl(f"def {cmd.name}(self): return self._properties.get('{cmd.name}', {cmd.default})")
    #     cog.outl(f"@{cmd.name}.setter")
    #     cog.outl(f"def {cmd.name}(self, value:{cmd.type}): self._properties['{cmd.name}'] = value")
    #     cog.outl(f"")
    # ]]]
    @property
    def basetexture(self): return self._properties.get('basetexture', None)
    @basetexture.setter
    def basetexture(self, value:Path): self._properties['basetexture'] = value

    @property
    def bumpmap(self): return self._properties.get('bumpmap', None)
    @bumpmap.setter
    def bumpmap(self, value:Path): self._properties['bumpmap'] = value

    @property
    def basetexture2(self): return self._properties.get('basetexture2', None)
    @basetexture2.setter
    def basetexture2(self, value:Path): self._properties['basetexture2'] = value

    @property
    def bumpmap2(self): return self._properties.get('bumpmap2', None)
    @bumpmap2.setter
    def bumpmap2(self, value:Path): self._properties['bumpmap2'] = value

    @property
    def envmap(self): return self._properties.get('envmap', None)
    @envmap.setter
    def envmap(self, value:Path): self._properties['envmap'] = value

    @property
    def envmapmask(self): return self._properties.get('envmapmask', None)
    @envmapmask.setter
    def envmapmask(self, value:Path): self._properties['envmapmask'] = value

    @property
    def detail(self): return self._properties.get('detail', None)
    @detail.setter
    def detail(self, value:Path): self._properties['detail'] = value

    @property
    def surfaceprop(self): return self._properties.get('surfaceprop', None)
    @surfaceprop.setter
    def surfaceprop(self, value:str): self._properties['surfaceprop'] = value

    @property
    def surfaceprop2(self): return self._properties.get('surfaceprop2', None)
    @surfaceprop2.setter
    def surfaceprop2(self, value:str): self._properties['surfaceprop2'] = value

    @property
    def additive(self): return self._properties.get('additive', False)
    @additive.setter
    def additive(self, value:bool): self._properties['additive'] = value

    @property
    def alphatest(self): return self._properties.get('alphatest', False)
    @alphatest.setter
    def alphatest(self, value:bool): self._properties['alphatest'] = value

    @property
    def envmapcontrast(self): return self._properties.get('envmapcontrast', False)
    @envmapcontrast.setter
    def envmapcontrast(self, value:bool): self._properties['envmapcontrast'] = value

    @property
    def envmapsaturation(self): return self._properties.get('envmapsaturation', False)
    @envmapsaturation.setter
    def envmapsaturation(self, value:bool): self._properties['envmapsaturation'] = value

    @property
    def nocull(self): return self._properties.get('nocull', False)
    @nocull.setter
    def nocull(self, value:bool): self._properties['nocull'] = value

    @property
    def nodecal(self): return self._properties.get('nodecal', False)
    @nodecal.setter
    def nodecal(self, value:bool): self._properties['nodecal'] = value

    @property
    def nolod(self): return self._properties.get('nolod', False)
    @nolod.setter
    def nolod(self, value:bool): self._properties['nolod'] = value

    @property
    def translucent(self): return self._properties.get('translucent', False)
    @translucent.setter
    def translucent(self, value:bool): self._properties['translucent'] = value

    @property
    def vertexalpha(self): return self._properties.get('vertexalpha', False)
    @vertexalpha.setter
    def vertexalpha(self, value:bool): self._properties['vertexalpha'] = value

    @property
    def vertexcolor(self): return self._properties.get('vertexcolor', False)
    @vertexcolor.setter
    def vertexcolor(self, value:bool): self._properties['vertexcolor'] = value

    # [[[end]]]

    def render(self):
        vmt = ""
        vmt += f"{self.shader}\n"
        vmt += "{\n"
        indent = "	"

        for key in self._properties.keys():
            value = self._properties[key]
            if type(value) is bool:
                value = 1 if value else 0
                
            try:
                value = json.dumps(value)
            except:
                value = json.dumps(str(value))
            vmt += indent+f"${key} {value}\n"

        vmt += "}\n"
        return vmt
    
    def write(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(self.render())