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
            }
        },
    }
}
"""
import copy
import json
import logging
import os
import time
from contextlib import contextmanager

from ansible_bender.builders.base import Build

DEFAULT_DATA = {
    "next_build_id": 1,
    "builds": {}
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
                logger.debug("ab is running as PID %s", pid)
                time.sleep(0.1)
            except FileNotFoundError:
                # cool, let's take the lock
                # FIXME: but this is not atomic, we should use open() for that
                with open(Database._lock_path(), "w") as fd:
                    fd.write("%s" % os.getpid())
                break
        yield True
        self.release()

    def release(self):
        """ release lock """
        os.unlink(self._lock_path())

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

    def record_build(self, build_i, build_state=None):
        """
        record build into database

        :param build_i: Build instance
        :param build_state: one of BuildState
        """
        with self.acquire():
            data = self._load()
            if build_state is not None:
                build_i.state = build_state
            if build_i.build_id is None:
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
            return Build.from_json(data["builds"][build_id])  # TODO: error checking
