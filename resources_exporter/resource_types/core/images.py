from os import stat
from pathlib import Path
from ... import utils
from ..resource_base import *

CFD = Path(__file__).parent.resolve()

class ImageResource(Resource):
    def export(self, **kwargs):
        return super().export(**kwargs)

    @staticmethod
    def get_extensions():
        return ["png", "bmp", "jpg", "jpeg"]

    @res_cmd("Create .psd version", "Copy and convert image into photoshop image")
    def convert_to_psd_cmd(self):
        src_filepath = self.filepath.resolve()
        dst_filepath = src_filepath.with_suffix(".psd")
        cmd = f'{self.config.image_magic_cmd} "{src_filepath}" "{dst_filepath}"'
        self.run_program(cmd)

    @staticmethod
    def get_icon() -> Path:
        return CFD/"icons/image.png"

class PhotoshopImage(ImageResource):
    def export(self, ico=False, **kwargs):
        self.export_png(self.filepath, self.dst_filepath)
        if ico: self.export_ico(self.filepath, self.dst_filepath)

    def export_png(self, src_filepath:Path, dst_filepath:Path):
        dst_filepath = dst_filepath.with_suffix(".png")
        utils.make_dirs_to_file(dst_filepath)

        def convert_to_png(dst_filepath):
            cmd = f'{self.config.image_magic_cmd} "{src_filepath}[0]" "{dst_filepath}"'
            self.run_program(cmd)

        convert_to_png(dst_filepath)
        print(f"converted \"{dst_filepath.name}\"")

        for glbfile in dst_filepath.parent.glob("*.glb"):
            add_path = Path(dst_filepath.with_stem(glbfile.stem+"_"+dst_filepath.stem))
            if add_path.exists():
                convert_to_png(add_path)
                print(f"also updated \"{add_path.name}\", probably for model \"{glbfile.name}\"")

        return dst_filepath

    def export_ico(self, src_filepath:Path, dst_filepath:Path):
        ico_filepath = dst_filepath.with_suffix(".ico")
        utils.make_dirs_to_file(dst_filepath)
        cmd = f'{self.config.image_magic_cmd} "{src_filepath}[0]" -define icon:auto-resize=128,64,48,32,16 "{ico_filepath}"'
        self.run_program(cmd)
        return ico_filepath

    # disable
    @res_cmd("", "", False)
    def convert_to_psd_cmd(self):
        pass

    @staticmethod
    def get_extensions():
        return ["psd"]

    @staticmethod
    def get_icon():
        return CFD/"icons/photoshop.png"

PhotoshopImage.add_setting("ico", "Create .ico file", "Export .ico")

class MaterialResource(Resource):
    @staticmethod
    def get_extensions():
        return []

    @staticmethod
    def get_icon():
        return CFD/"icons/material.png"