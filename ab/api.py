from ab.builder import get_builder
from ab.core import AnsibleRunner


class Application:
    def __init__(self, playbook_path, base_image, target_image, builder_name, metadata):
        """
        :param playbook_path: str, path to playbook
        :param base_image: str, name of the base image
        :param target_image: str, name of the newly built image
        :param builder_name: str, name of the builder to pick
        :param metadata: instance of ImageMetadata
        """
        self.builder = get_builder(builder_name)(base_image, target_image, metadata)
        self.a_runner = AnsibleRunner(playbook_path, self.builder)

    def build(self):
        # TODO: clean working container, also make that configurable
        self.builder.create()
        self.a_runner.build()
        self.builder.commit()
