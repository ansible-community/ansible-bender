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
import json
import logging
import os

DEFAULT_DATA = {
    "next_build_id": 1,
    "builds": {}
}


logger = logging.getLogger(__name__)


class Database:
    """ Simple implementation of persistent data store for ab; it's just a locked json file  """

    def __init__(self):
        self._data = {}  # the gold
        self.load()

    @classmethod
    def acquire(cls):
        """
        get access to database; only one instance of ab can access database
        """
        try:
            with open(Database._lock_path(), "r") as fd:
                # the file exists, ab is running
                pid = fd.read()
                logger.info("ab is running as PID %s", pid)
            raise RuntimeError("ab is already running as PID {}, "
                               "this is being tracked by pidfile {}".format(pid, cls._lock_path()))
        except FileNotFoundError:
            # cool, let's take the lock
            with open(Database._lock_path(), "w") as fd:
                fd.write("%s" % os.getpid())
        return Database()

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

    def load(self):
        """ load data from disk """
        try:
            with open(self._db_path(), "r") as fd:
                self._data = json.load(fd)
        except FileNotFoundError:
            # no problem, probably a first run
            logger.debug("initializing database")
            self._data = DEFAULT_DATA

    def save(self):
        """ save data from memory to disk """
        with open(self._db_path(), "w") as fd:
            json.dump(self._data, fd, indent=2)

    def _get_and_bump_build_id(self):
        """ return id for next build id and increment the one in DB """
        next_build_id = self._data["next_build_id"]
        self._data["next_build_id"] += 1
        return next_build_id

    def record_build(self, build_i):
        """
        record build into database

        :param build_i: Build instance
        """
        build_i.build_id = self._get_and_bump_build_id()
        self._data["builds"][build_i.build_id] = build_i.to_dict()
        return build_i
