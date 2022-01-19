from pathlib import Path
from resources_exporter.resource_types.resource_base import ExportConfig, Resource

class AudioResource(Resource):
    def export(self, **kwargs):
        return super().export()

    @staticmethod
    def get_extensions():
        return ["mp3", "wav", "ogg"]