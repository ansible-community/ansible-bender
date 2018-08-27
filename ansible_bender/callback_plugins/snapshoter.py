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
        :return:
        """
        build_id = os.environ["AB_BUILD_ID"]
        task_name = task_result.task_name.encode("utf-8")
        a = Application()
        image_name = a.cache_task_result(task_name, build_id=build_id)
        self._display.display("caching task result in image '%s'" % image_name)

    def _load_from_cache(self):
        """
        load image state from cache

        :return:
        """

    def v2_on_any(self, *args, **kwargs):
        # TODO: before running a task, check cache; try to control this with tags: never-cache
        try:
            first_arg = args[0]
        except IndexError:
            return
        if isinstance(first_arg, TaskResult):
            return self._snapshot(first_arg)
