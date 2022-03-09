from pathlib import Path
from ..resource_base import *

CFD = Path(__file__).parent.resolve()

class AudioResource(Resource):
    def export(self, **kwargs):
        return super().export()

    @staticmethod
    def get_extensions():
        return ["mp3", "wav", "ogg"]

    @staticmethod
    def get_icon() -> Path:
        return CFD/"icons/sound.png"