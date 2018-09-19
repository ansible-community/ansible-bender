import logging
import os
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
        self.db = Database()

    def build(self, playbook_path, build, build_volumes=None):
        """
        build container image

        :param playbook_path: str, path to playbook
        :param build: instance of Build
        :param build_volumes: list of str, bind-mount specification: ["/host:/cont", ...]
        """
        if not os.path.isfile(playbook_path):
            raise RuntimeError("No such file or directory: %s" % playbook_path)

        # record as soon as possible
        self.db.record_build(build)

        builder = self.get_builder(build)
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
                self.db.record_build(None, build_id=build.build_id, build_state=BuildState.FAILED)
                # TODO: let this be done by the callback plugin
                image_name = build.target_image + "-failed"
                builder.commit(image_name)
                out_logger.info("Image build failed /o\\")
                out_logger.info("The progress is saved into image '%s'", image_name)
                raise

            self.db.record_build(None, build_id=build.build_id, build_state=BuildState.DONE)
            builder.commit(build.target_image)
            out_logger.info("Image '%s' was built successfully \o/",  build.target_image)
        finally:
            builder.clean()

    def get_builder(self, build):
        return get_builder(build.builder_name)(build, debug=self.debug)

    def maybe_load_from_cache(self, content, build_id):
        build = self.db.get_build(build_id)
        builder = self.get_builder(build)

        if not build.cache_tasks:
            return

        if build.progress:
            last_item = build.progress[-1]
            base_image_id = last_item["image_id"]
        else:
            base_image_id = builder.get_image_id(build.base_image)
        layer_id = self.get_layer(content, base_image_id)
        if layer_id:
            builder = self.get_builder(build)
            build.base_layer = layer_id
            builder.swap_working_container()
        return layer_id

    def get_layer(self, content, base_image_id):
        return self.db.get_cached_layer(content, base_image_id)

    def record_progress(self, build, content, layer_id, build_id=None):
        if build_id:
            build = self.db.get_build(build_id)
        builder = self.get_builder(build)
        if build.progress:
            last_item = build.progress[-1]
            base_image_id = last_item["image_id"]
        else:
            base_image_id = builder.get_image_id(build.base_image)
        if not layer_id:
            # skipped task, not cached
            layer_id = self.get_layer(content, base_image_id) or base_image_id
        build.append_progress(content, layer_id, base_image_id)
        self.db.record_build(build)
        return base_image_id

    def cache_task_result(self, content, build_id):
        """ snapshot the container after a task was executed """
        build = self.db.get_build(build_id)
        if not build.cache_tasks:
            return
        timestamp = datetime.datetime.now().strftime("%Y%M%d-%H%M%S")
        image_name = "%s-%s" % (build.target_image, timestamp)
        # buildah doesn't accept upper case
        image_name = image_name.lower()
        builder = self.get_builder(build)
        # FIXME: do not commit metadata, just filesystem
        layer_id = builder.commit(image_name)
        base_image_id = self.record_progress(build, content, layer_id)
        self.db.save_layer(layer_id, base_image_id, content)
        return image_name

    def clean(self):
        self.db.release()