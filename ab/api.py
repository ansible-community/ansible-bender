import logging

from ab.builder import get_builder
from ab.constants import OUT_LOGGER
from ab.core import AnsibleRunner


out_logger = logging.getLogger(OUT_LOGGER)


class Application:
    def __init__(self, playbook_path, base_image, target_image, builder_name, metadata,
                 debug=False):
        """
        :param playbook_path: str, path to playbook
        :param base_image: str, name of the base image
        :param target_image: str, name of the newly built image
        :param builder_name: str, name of the builder to pick
        :param metadata: instance of ImageMetadata
        :param debug: bool, provide debug output if True
        """
        # TODO: I think people will want to pick python interpreter via CLI
        self.debug = debug
        self.target_image = target_image
        self.builder = get_builder(builder_name)(base_image, target_image, metadata, debug=debug)
        self.a_runner = AnsibleRunner(playbook_path, self.builder, debug=debug)

    def build(self, build_volumes=None):
        """
        build container image

        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        if not self.builder.is_base_image_present():
            self.builder.pull()
        self.builder.create(build_volumes=build_volumes)
        try:
            self.a_runner.build(python_interpreter=self.builder.find_python_interpreter())
            self.builder.commit()
            out_logger.info("Image '%s' was built successfully \o/",  self.target_image)
        finally:
            # TODO: make cleanup configurable
            self.builder.clean()
