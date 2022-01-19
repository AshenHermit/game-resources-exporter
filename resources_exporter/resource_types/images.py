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
        dst_filepath = self.dst_filepath.with_suffix(".png")
        self.make_dirs_to_file(dst_filepath)
        cmd = f'{self.config.image_magic_cmd} "{self.filepath}[0]" "{dst_filepath}"'
        self.run_command(cmd)

        if ico:
            dst_filepath = dst_filepath.with_suffix(".ico")
            cmd = f'{self.config.image_magic_cmd} "{self.filepath}[0]" -define icon:auto-resize=128,64,48,32,16 "{dst_filepath}"'
            self.run_command(cmd)

    @staticmethod
    def get_extensions():
        return ["psd"]