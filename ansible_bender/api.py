import logging
import os
import base64
import datetime

from ansible_bender.builder import get_builder
from ansible_bender.builders.base import BuildState
from ansible_bender.constants import OUT_LOGGER
from ansible_bender.core import AnsibleRunner
from ansible_bender.db import Database
from ansible_bender.exceptions import AbBuildUnsuccesful

out_logger = logging.getLogger(OUT_LOGGER)


class Application:
    def __init__(self, debug=False):
        """
        :param debug: bool, provide debug output if True
        """
        self.debug = debug
        self.db = Database.acquire()

    def build(self, playbook_path, build, build_volumes=None):
        """
        build container image

        :param playbook_path: str, path to playbook
        :param build: instance of Build
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        if not os.path.isfile(playbook_path):
            raise RuntimeError("No such file or directory: %s" % playbook_path)

        builder = get_builder(build.builder_name)(build, debug=self.debug)
        a_runner = AnsibleRunner(playbook_path, builder, build, debug=self.debug)

        self.db.record_build(build, build_state=BuildState.IN_PROGRESS)

        if not builder.is_base_image_present():
            builder.pull()
        py_intrprtr = builder.find_python_interpreter()

        builder.create(build_volumes=build_volumes)

        try:
            try:
                a_runner.build(python_interpreter=py_intrprtr)
            except AbBuildUnsuccesful:
                self.db.record_build(build, build_state=BuildState.FAILED)
                # TODO: let this be done by the callback plugin
                image_name = build.target_image + "-failed"
                builder.commit(image_name)
                out_logger.info("Image build failed /o\\")
                out_logger.info("The progress is saved into image '%s'", image_name)
                raise

            self.db.record_build(build, build_state=BuildState.DONE)
            builder.commit(build.target_image)
            out_logger.info("Image '%s' was built successfully \o/",  build.target_image)
        finally:
            builder.clean()

    def cache_task_result(self, task_name, build_id):
        """ snapshot the container after a task was executed """
        if isinstance(build_id, str):
            build_id = int(build_id)
        build = self.db.get_build(build_id)
        # TODO: load build, initiated builder and commit, log results
        # TODO: add here whole task code and task result and also hash referenced files
        layer_hash = base64.b64encode(task_name)[:8]
        timestamp = datetime.datetime.now().strftime("%Y%M%d-%H%M%S")
        image_name = "%s-%s-%s" % (build.target_image, layer_hash, timestamp)
        builder_kls = get_builder(build.builder_name)
        builder = builder_kls(build, debug=self.debug)
        builder.commit(image_name)
        return image_name

    def clean(self):
        self.db.save()
        self.db.release()
