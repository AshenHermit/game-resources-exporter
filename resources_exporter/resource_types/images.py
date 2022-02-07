from os import stat
from .. import utils
from pathlib import Path
from resources_exporter.resource_types.resource_base import ExportConfig, Resource

class ImageResource(Resource):
    def export(self, **kwargs):
        return super().export(**kwargs)

    @staticmethod
    def get_extensions():
        return ["png", "bmp", "jpg", "jpeg"]

class PhotoshopImage(ImageResource):
    def export(self, ico=False, **kwargs):
        self.export_png(self.filepath, self.dst_filepath, ico)

    def export_png(self, src_filepath:Path, dst_filepath:Path, ico=False):
        dst_filepath = dst_filepath.with_suffix(".png")
        utils.make_dirs_to_file(dst_filepath)
        cmd = f'{self.config.image_magic_cmd} "{src_filepath}[0]" "{dst_filepath}"'
        self.run_command(cmd)

        if ico:
            ico_filepath = dst_filepath.with_suffix(".ico")
            cmd = f'{self.config.image_magic_cmd} "{src_filepath}[0]" -define icon:auto-resize=128,64,48,32,16 "{ico_filepath}"'
            self.run_command(cmd)

        return dst_filepath

    @staticmethod
    def get_extensions():
        return ["psd"]