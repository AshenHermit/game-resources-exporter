from email.mime import base
from ...resource_types import *

class SourceMaterialFile(Resource):
    @staticmethod
    def get_extensions():
        return ["vmt"]

class SourceImageResource(ImageResource):
    @property
    def vtfcmd_executable(self):
        return self.config.get("vtfcmd_executable", "VTFCmd.exe", True)

    @staticmethod
    def format_to_normalmap(path:Path):
        path = Path(path)
        return path.with_name(path.with_suffix("").name+"_normal"+path.suffix)
    @property
    def has_normal_map(self):
        return self.format_to_normalmap(self.filepath).exists()
    @property
    def is_normal_map(self):
        return self.filepath.name == self.format_to_normalmap(self.filepath).name

    def try_write_vmt(self):
        if self.filepath.with_suffix(".vmt").exists(): return
        if self.is_normal_map: return

        texture_path = self.dst_filepath\
            .relative_to(self.config.output_root/"materials")\
            .with_suffix("").as_posix()
        vmt = ""
        vmt += '"VertexLitGeneric"\n'
        vmt += '{\n'
        vmt += f'    "$baseTexture" "{texture_path}"\n'
        if self.has_normal_map:
            vmt += f'    "$bumpmap" "{self.format_to_normalmap(texture_path)}"\n'
        vmt += '}\n'

        dst_filepath = self.dst_filepath.with_suffix(".vmt")
        utils.make_dirs_to_file(dst_filepath)
        dst_filepath.write_text(vmt)
        return dst_filepath

    def export_vtf(self, src_filepath:Path, dst_filepath:Path):
        dst_filepath = dst_filepath.with_suffix(".vtf")
        utils.make_dirs_to_file(dst_filepath)
        cmd = f"\"{self.vtfcmd_executable}\" -file \"{src_filepath}\" -resize -output \"{dst_filepath.parent}\""
        self.run_command(cmd)
        return dst_filepath

    def export(self, **kwargs):
        if self.filepath.suffix == ".vtf":
            super().export(**kwargs)
        else:
            self.export_vtf(self.filepath, self.dst_filepath.with_suffix(".vtf"))
        self.try_write_vmt()

    @staticmethod
    def get_extensions():
        return ImageResource.get_extensions() + ["vtf"]

class SourcePhotoshopImage(PhotoshopImage, SourceImageResource):
    def export(self, ico=False, **kwargs):
        png_filepath = self.filepath.with_suffix(".png")
        self.export_png(self.filepath, self.filepath.with_suffix(".png"), ico)
        self.export_vtf(png_filepath, self.dst_filepath.with_suffix(".vtf"))
        os.remove(str(png_filepath))
        self.try_write_vmt()