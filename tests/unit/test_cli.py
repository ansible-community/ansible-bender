import pytest

from ansible_bender.cli import split_once_or_fail_with


def test_split_once():
    secret = "banana"
    with pytest.raises(RuntimeError, match=secret):
        split_once_or_fail_with("a-a-a", "=", secret)
    assert ("a", "a") == split_once_or_fail_with("a=a", "=", secret)
