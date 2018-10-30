from ansible_bender.utils import run_cmd


def test_run_cmd():
    assert "etc" in run_cmd(["ls", "-1", "/"], return_all_output=True)
