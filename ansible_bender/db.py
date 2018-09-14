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
            progress: [
                {content: "", base_image_id: "", image_id: ""}
            ]
        },
    },
    "store": {
        "base-image-id": {
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
import traceback
from contextlib import contextmanager

from ansible_bender.builders.base import Build

DEFAULT_DATA = {
    "next_build_id": 1,
    "builds": {},
    "store": {}
}


logger = logging.getLogger(__name__)


class Database:
    """ Simple implementation of persistent data store for ab; it's just a locked json file  """

    def __init__(self):
        # we can't cache the data
        pass

    @contextmanager
    def acquire(self):
        """
        lock usage of database
        """
        while True:
            try:
                with open(Database._lock_path(), "r") as fd:
                    # the file exists, ab changes the database
                    pid = fd.read()
                logger.info("ab is running as PID %s", pid)
                logger.debug("stack trace: %s", traceback.extract_stack())
                time.sleep(0.1)
            except FileNotFoundError:
                # cool, let's take the lock
                # FIXME: but this is not atomic, we should use open() for that
                with open(Database._lock_path(), "w") as fd:
                    fd.write("%s" % os.getpid())
                break
        logger.debug("this stack has the lock: %s", traceback.extract_stack())
        yield True
        self.release()

    def release(self):
        """ release lock """
        try:
            os.unlink(self._lock_path())
        except FileNotFoundError:
            pass

    @staticmethod
    def _runtime_dir_path():
        candidates = [
            os.environ.get("XDG_RUNTIME_DIR", None),
            "~/.cache",
            "/var/tmp"
        ]
        for c in candidates:
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
        return our_dir

    @staticmethod
    def _db_path():
        data_path = os.path.join(Database._runtime_dir_path(), "db.json")
        logger.debug("DB path is %s", data_path)
        return data_path

    @staticmethod
    def _lock_path():
        lock_path = os.path.join(Database._runtime_dir_path(), "ab.pid")
        logger.debug("lock path is %s", lock_path)
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

    def _load_build(self, data, build_id):
        return Build.from_json(data["builds"][build_id])  # TODO: error checking

    def _save(self, data):
        """ save data from memory to disk, lock has to be acquired already! """
        with open(self._db_path(), "w") as fd:
            json.dump(data, fd, indent=2)

    @staticmethod
    def _get_and_bump_build_id(data):
        """ return id for next build id and increment the one in DB """
        next_build_id = data["next_build_id"]
        data["next_build_id"] += 1
        return str(next_build_id)

    def record_build(self, build_i, build_id=None, build_state=None):
        """
        record build into database

        :param build_i: Build instance
        :param build_id: str, id of the build to load from DB
        :param build_state: one of BuildState
        """
        with self.acquire():
            data = self._load()
            if build_id is not None:
                build_i = self._load_build(data, build_id)
            if build_state is not None:
                build_i.state = build_state
            if build_i.build_id is None:
                timestamp = datetime.datetime.now().strftime("-%Y%M%d-%H%M%S%f")
                build_i.build_container = build_i.target_image + timestamp + "-cont"
                build_i.build_id = self._get_and_bump_build_id(data)
            data["builds"][build_i.build_id] = build_i.to_dict()
            self._save(data)

    def get_build(self, build_id):
        """
        get Build instance by selected build_id

        :param build_id: int, build_id
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
