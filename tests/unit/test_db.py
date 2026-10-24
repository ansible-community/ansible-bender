import os

import pytest

from ansible_bender.db import Database


def test_acquire_releases_lock_when_body_raises(tmp_path):
    db = Database(db_path=str(tmp_path))
    lock_path = db._lock_path()

    with pytest.raises(RuntimeError, match="expected failure"):
        with db.acquire():
            assert os.path.exists(lock_path)
            raise RuntimeError("expected failure")

    assert not os.path.exists(lock_path)
