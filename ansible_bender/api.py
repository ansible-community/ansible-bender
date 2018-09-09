import logging
import os

from ansible_bender.builder import get_builder
from ansible_bender.builders.base import BuildState
from ansible_bender.constants import OUT_LOGGER
from ansible_bender.core import AnsibleRunner
from ansible_bender.db import Database
from ansible_bender.exceptions import AbBuildUnsuccesful

out_logger = logging.getLogger(OUT_LOGGER)


class Application:
    def __init__(self, playbook_path, build, debug=False):
        """
        :param playbook_path: str, path to playbook
        :param build: instance of Build
        :param debug: bool, provide debug output if True
        """
        self.debug = debug
        self.build_i = build
        self.target_image = self.build_i.target_image  # FIXME: remove this likely

        if not os.path.isfile(playbook_path):
            raise RuntimeError("No such file or directory: %s" % playbook_path)

        self.db = Database.acquire()

        self.builder = get_builder(self.build_i.builder_name)(self.build_i, debug=debug)
        self.a_runner = AnsibleRunner(playbook_path, self.builder, debug=debug)

    def build(self, build_volumes=None):
        """
        build container image

        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        self.db.record_build(self.build_i)
        if not self.builder.is_base_image_present():
            self.builder.pull()
        self.builder.create(build_volumes=build_volumes)

        try:
            py_intrprtr = self.builder.find_python_interpreter()

            self.build_i.state = BuildState.IN_PROGRESS
            self.db.record_build(self.build_i)
            try:
                self.a_runner.build(python_interpreter=py_intrprtr)
            except AbBuildUnsuccesful:
                self.build_i.state = BuildState.FAILED
                self.db.record_build(self.build_i)
                image_name = self.target_image + "-failed"
                self.builder.commit(image_name)
                out_logger.info("Image build failed /o\\")
                out_logger.info("The progress is saved into image '%s'", image_name)
                raise

            self.build_i.state = BuildState.DONE
            self.db.record_build(self.build_i)
            self.builder.commit(self.target_image)
            out_logger.info("Image '%s' was built successfully \o/",  self.target_image)
        finally:
            self.builder.clean()

    def clean(self):
        self.db.save()
        self.db.release()
