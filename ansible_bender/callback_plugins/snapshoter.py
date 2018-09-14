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

    def _snapshot(self, task_result):
        """
        snapshot the target container

        :param task_result: instance of TaskResult
        """
        if task_result._task.action == "setup":
            # we ignore setup
            return
        build_id = os.environ["AB_BUILD_ID"]
        a = Application()
        content = self.get_task_content(task_result._task.get_ds())
        if task_result.is_skipped() or getattr(task_result, "_result", {}).get("skip_reason", False):
            self._display.display("recoding cache hit")
            a.record_progress(None, content, None, build_id=build_id)
            return
        image_name = a.cache_task_result(content, build_id=build_id)
        self._display.display("caching task result in image '%s'" % image_name)

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
        build_id = os.environ["AB_BUILD_ID"]
        a = Application()
        content = self.get_task_content(task.get_ds())
        status = a.maybe_load_from_cache(content, build_id=build_id)
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
