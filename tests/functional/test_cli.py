from .test_buildah import ab
from ..spellbook import basic_playbook_path, base_image
from ansible_bender.constants import PLAYBOOK_TEMPLATE
from ansible_bender.utils import run_cmd

def test_inspect_cmd(tmpdir, target_image):
    workdir_path = "/etc"
    l_a_b = "A=B"
    l_x_y = "x=y"
    e_a_b = "A=B"
    e_x_y = "X=Y"
    cmd, cmd_e = "ls -lha", ["ls", "-lha"]
    entrypoint = "ls -lha"
    # FIXME
    # user = "1000"
    p_80, p_443 = "80", "443"
    runtime_volume = "/var/lib/asdqwe"
    cmd = ["build",
           "-w", workdir_path,
           "-l", l_a_b, l_x_y,
           "-e", e_a_b, e_x_y,
           "--cmd", cmd,
           "--entrypoint", entrypoint,
           # "-u", user,
           "-p", p_80, p_443,
           "--runtime-volumes", runtime_volume,
           "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd, str(tmpdir))
    out = ab(["inspect"], str(tmpdir), return_output=True)

    assert "base_image: quay.io/biocontainers/python:3" in out
    assert "build_container: " in out
    assert "build_finished_time: " in out
    assert "build_start_time: " in out
    assert "build_id: " in out
    assert "builder_name: buildah" in out
    assert "cache_tasks: true" in out
    assert "layers:" in out
    assert "- base_image_id: null" in out
    assert "  content: " in out
    assert "  layer_id: " in out
    assert "state: done" in out
    assert "target_image: " in out
    metadata = """\
metadata:
  annotations: {}
  cmd: ls -lha
  entrypoint: ls -lha
  env_vars:
    A: B
    X: Y
  labels:
    A: B
    x: y
  ports:
  - '80'
  - '443'
  user: null
  volumes:
  - /var/lib/asdqwe
  working_dir: /etc"""
    assert metadata in out


def test_get_logs(target_image, tmpdir):
    cmd = ["build", basic_playbook_path, base_image, target_image]
    ab(cmd, str(tmpdir))
    out = ab(["get-logs"], str(tmpdir), return_output=True).lstrip()
    assert "PLAY [registry" in out
    assert "TASK [Gathering Facts]" in out
    assert "failed=0" in out
    assert "TASK [print local env vars]" in out


def test_clean(target_image, tmpdir):
    cmd = ["build", basic_playbook_path, base_image, target_image]
    ab(cmd, str(tmpdir))
    run_cmd(["podman", "rmi", target_image], print_output=True)
    cmd = ["clean"]
    ab(cmd, str(tmpdir))
    out = ab(["clean"], str(tmpdir), return_output=True)
    assert out.startswith("Cleaning images from database which are no longer present on the disk...")
    assert out.endswith("Done!\n")


def test_init(tmpdir):
    cmd = ["init"]
    ab(cmd, str(tmpdir))
    out = ab(["init"], str(tmpdir), return_output=True)
    assert out.startswith("Created an Ansible playbook template as playbook.yml")
    with open('playbook.yml', 'r') as fd:
      pb = fd.read()
    assert pb == PLAYBOOK_TEMPLATE
