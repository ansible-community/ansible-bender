import logging
import os

from ansible_bender.builder import get_builder
from ansible_bender.constants import OUT_LOGGER
from ansible_bender.core import AnsibleRunner
from ansible_bender.exceptions import AbBuildUnsuccesful

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

        if not os.path.isfile(playbook_path):
            raise RuntimeError("No such file or directory: %s" % playbook_path)

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

        py_intrprtr = self.builder.find_python_interpreter()
        failed = False
        failure_exc = None
        try:
            self.a_runner.build(python_interpreter=py_intrprtr)
        except AbBuildUnsuccesful as ex:
            failed = True
            failure_exc = ex

        image_name = self.target_image
        if failed:
            image_name = self.target_image + "-failed"
            self.builder.commit(image_name)
            out_logger.info("Image build failed /o\\")
            out_logger.info("The progress is saved into image '%s'", image_name)
        else:
            self.builder.commit(image_name)
            out_logger.info("Image '%s' was built successfully \o/",  image_name)
        self.builder.clean()

        if failed and failure_exc:
            raise failure_exc
