import hashlib
import json
import os

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import TaskResult
from ansible_bender.api import Application


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'a_container_image_snapshoter'
    CALLBACK_NEEDS_WHITELIST = True

    def _get_app_and_build(self):
        build_id = os.environ["AB_BUILD_ID"]
        db_path = os.environ["AB_DB_PATH"]
        app = Application(init_logging=False, db_path=db_path)
        build = app.get_build(build_id)
        app.set_logging(debug=build.debug, verbose=build.verbose)
        return app, build

    def _snapshot(self, task_result):
        """
        snapshot the target container

        :param task_result: instance of TaskResult
        """
        if task_result._task.action == "setup":
            # we ignore setup
            return
        if task_result.is_failed() or task_result._result.get("rc", 0) > 0:
            return
        a, build = self._get_app_and_build()
        content = self.get_task_content(task_result._task.get_ds())
        if task_result.is_skipped() or getattr(task_result, "_result", {}).get("skip_reason", False):
            a.record_progress(None, content, None, build_id=build.build_id)
            return
        image_name = a.cache_task_result(content, build_id=build.build_id)
        if image_name:
            self._display.display("caching the task result in an image '%s'" % image_name)

    @staticmethod
    def get_task_content(serialized_data):
        assert serialized_data
        c = json.dumps(serialized_data, sort_keys=True).encode("utf-8")
        m = hashlib.sha512(c)
        return m.hexdigest()

    def _maybe_load_from_cache(self, task):
        """
        load image state from cache

        :param task: instance of Task
        """
        # TODO: try to control caching with tags: never-cache
        if task.action == "setup":
            # we ignore setup
            return
        a, build = self._get_app_and_build()
        content = self.get_task_content(task.get_ds())
        status = a.maybe_load_from_cache(content, build_id=build.build_id)
        if status:
            self._display.display("loaded from cache: '%s'" % status)
            task.when = "0"  # skip

    def v2_playbook_on_task_start(self, task, is_conditional):
        return self._maybe_load_from_cache(task)

    def v2_on_any(self, *args, **kwargs):
        try:
            first_arg = args[0]
        except IndexError:
            return
        if isinstance(first_arg, TaskResult):
            return self._snapshot(first_arg)
