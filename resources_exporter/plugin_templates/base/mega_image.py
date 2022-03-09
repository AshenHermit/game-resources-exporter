from ...resource_types import *

class MegaImage(ImageResource):
    def export(self, **kwargs):
        dst_filepath = self.filepath.with_suffix(".png")
        utils.make_dirs_to_file(dst_filepath)

        color = self.filepath.read_text()
        cmd = f"\"{self.config.image_magic_cmd}\" -size 64x64 xc:\"{color}\" \"{dst_filepath}\""
        self.run_program(cmd)

    @res_cmd("Turn into mega color", "")
    def make_black_cmd(self):
        self.filepath.write_text("#50ffc7")

    @staticmethod
    def get_extensions():
        return ["color"]