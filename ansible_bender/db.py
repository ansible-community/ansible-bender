"""
A database module. A class to manage ab's persistent data.


# The schema

{
    "next_build_id": int  #
    "builds": {
        <id>: {
            state: ...
            base_image: ...
            target_image: ...
            builder_name: ...
            metadata: {
                command: ...
                user: ...
                env: ...
                ...
            },
            layers: [
                Layer(content, layer_id, base_image_id, cached),
            ]
            layer_index: {
                layer_id: layer
            }
        },
    },
    "store": {
        "base-image-id": {  # base-image + content = new image
            content: {
                image_id:
            }
        }
    }
}
"""
import copy
import datetime
import json
import logging
import os
import time
from contextlib import contextmanager

from ansible_bender.conf import Build
from ansible_bender.constants import TIMESTAMP_FORMAT

DEFAULT_DATA = {
    "next_build_id": 1,
    "builds": {},
    "store": {}
}

PATH_CANDIDATES = [
    "~/.cache",
    os.environ.get("XDG_RUNTIME_DIR", ""),
    "/var/tmp"
]

logger = logging.getLogger(__name__)


def generate_working_cont_name(image_name):
    timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
    san = image_name.replace(".", "-").replace(":", "-").replace("/", "-")
    return f"{san}-{timestamp}-cont"


class Database:
    """ Simple implementation of persistent data store for ab; it's just a locked json file """

    def __init__(self, db_path=None):
        path_preference = PATH_CANDIDATES.copy()
        if db_path:
            path_preference.insert(0, db_path)
        self.runtime_dir_path, self.db_root_path = self._runtime_dir_path(path_preference)

    @contextmanager
    def acquire(self):
        """
        lock usage of database
        """
        while True:
            try:
                with open(self._lock_path(), "r") as fd:
                    # the file exists, ab changes the database
                    pid = fd.read()
                logger.info("ab is running as PID %s", pid)
                # logger.debug("stack trace: %s", traceback.extract_stack())
                time.sleep(0.1)
            except FileNotFoundError:
                # cool, let's take the lock
                # FIXME: but this is not atomic, we should use open() for that
                with open(self._lock_path(), "w") as fd:
                    fd.write("%s" % os.getpid())
                break
        # logger.debug("this stack has the lock: %s", traceback.extract_stack())
        yield True
        self.release()

    def release(self):
        """ release lock """
        try:
            os.unlink(self._lock_path())
        except FileNotFoundError:
            pass

    @staticmethod
    def _runtime_dir_path(path_preference):
        logger.debug("search for runtime dir")
        for c in path_preference:
            logger.debug("trying %s", c)
            if not c:
                continue
            resolved = os.path.abspath(os.path.expanduser(c))
            if os.path.isdir(resolved):
                break
        else:
            raise RuntimeError("Can't find a suitable directory to store runtime data.")
        logger.debug("runtime dir is %s", resolved)
        our_dir = os.path.join(resolved, "ab")
        os.makedirs(our_dir, mode=0o0700, exist_ok=True)
        return our_dir, resolved

    def _db_path(self):
        data_path = os.path.join(self.runtime_dir_path, "db.json")
        return data_path

    def _lock_path(self):
        lock_path = os.path.join(self.runtime_dir_path, "ab.pid")
        return lock_path

    def _load(self):
        """ load data from disk, lock has to be acquired already! """
        try:
            with open(self._db_path(), "r") as fd:
                return json.load(fd)
        except FileNotFoundError:
            # no problem, probably a first run
            logger.debug("initializing database")
            return copy.deepcopy(DEFAULT_DATA)

    @staticmethod
    def _load_build(data, build_id):
        try:
            return Build.from_json(data["builds"][build_id])
        except KeyError:
            raise RuntimeError("There is no such build with ID %s" % build_id)

    def _save(self, data):
        """ save data from memory to disk, lock has to be acquired already! """
        with open(self._db_path(), "w") as fd:
            json.dump(data, fd, indent=2)

    @staticmethod
    def _get_and_bump_build_id(data):
        """ return id for next build id and increment the one in DB """
        next_build_id = data["next_build_id"]
        data["next_build_id"] += 1
        # TODO: verify such build is not in DB, we don't want to overwrite, just in case
        return str(next_build_id)

    def record_build(self, build_i, build_id=None, build_state=None, set_finish_time=False):
        """
        record build into database

        :param build_i: Build instance
        :param build_id: str, id of the build to load from DB
        :param build_state: one of BuildState
        :param set_finish_time: bool, set build_finish_time to current time
        """
        with self.acquire():
            data = self._load()
            if build_id is not None:
                build_i = self._load_build(data, build_id)
            if build_state is not None:
                build_i.state = build_state
            if build_i.build_id is None:
                build_i.build_container = generate_working_cont_name(build_i.target_image)
                build_i.build_id = self._get_and_bump_build_id(data)
            if set_finish_time:
                build_i.build_finished_time = datetime.datetime.now()
            data["builds"][build_i.build_id] = build_i.to_dict()
            self._save(data)
        return build_i

    def get_latest_build(self):
        """
        return build with highest ID

        :return: build
        """
        with self.acquire():
            data = self._load()
            build_id = str(data["next_build_id"] - 1)
            return self._load_build(data, build_id)

    def get_build(self, build_id):
        """
        get Build instance by selected build_id

        :param build_id: str
        :return: instance of Build
        """
        with self.acquire():
            data = self._load()
            return self._load_build(data, build_id)

    def save_layer(self, layer_id, base_image, content):
        with self.acquire():
            data = self._load()
            store = data["store"]
            store.setdefault(base_image, {})
            store[base_image].setdefault(content, {})
            store[base_image][content]["image_id"] = layer_id
            self._save(data)

    def get_cached_layer(self, content, base_image_id):
        with self.acquire():
            data = self._load()
            store = data["store"]
            try:
                return store[base_image_id][content]["image_id"]
            except KeyError:
                return

    def load_builds(self):
        """
        provide a list of all available builds

        :return: a list of Build instances
        """
        with self.acquire():
            data = self._load()
            return [Build.from_json(b) for b in data["builds"].values()]
