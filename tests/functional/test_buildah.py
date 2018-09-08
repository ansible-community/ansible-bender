"""
Make sure that we can build using buildah builder.
"""
import os
import re
import random
import string
import subprocess

import pytest

from ansible_bender.builders.buildah_builder import buildah, inspect_buildah_resource

this_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(this_dir))
data_dir = os.path.join(this_dir, "data")


def random_word(length):
    # https://stackoverflow.com/a/2030081/909579
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def ab(args, debug=True, return_output=False):
    """
    python3 -m ab.cli -v build ./playbook.yaml registry.fedoraproject.org/fedora:28 asdqwe-image

    :return:
    """
    cmd = ["python3", "-m", "ansible_bender.cli"]
    if debug:
        cmd += ["--debug"]
    if return_output:
        return subprocess.check_output(cmd + args, cwd=project_dir, universal_newlines=True)
    else:
        # don't use run_cmd here, it makes things complicated
        subprocess.check_call(cmd + args, cwd=project_dir)


def test_output():
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", basic_playbook_path, base_image, target_image]
    out = ab(cmd, return_output=True, debug=False)
    try:
        assert 'Getting image source signatures' in out
        assert not re.match(r'ERROR\s+Getting image source signatures', out)
        assert 'Copying blob' in out
        assert not re.match(r'ERROR\s+Copying blob', out)
        buildah("inspect", ["-t", "image", target_image])
    finally:
        buildah("rmi", [target_image])


def test_build_basic_image():
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    # TODO: pick smaller image: python3 & alpine
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", basic_playbook_path, base_image, target_image]
    ab(cmd)
    buildah("inspect", ["-t", "image", target_image])
    buildah("rmi", [target_image])


def test_build_basic_image_with_env_vars():
    a_b = "A=B"
    x_y = "X=Y"
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", "-e", a_b, x_y, "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd)
    out = inspect_buildah_resource("image", target_image)
    assert a_b in out["OCIv1"]["config"]["Env"]
    assert x_y in out["OCIv1"]["config"]["Env"]
    # TODO: also run container and make sure that the env var is set inside the container
    buildah("rmi", [target_image])


def test_build_basic_image_with_wrong_env_vars():
    la_la_la = "AB-LA-BLA-LA-LA-BLA"
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", "-e", la_la_la, "--", basic_playbook_path, base_image, target_image]
    with pytest.raises(subprocess.CalledProcessError) as exc:
        ab(cmd)
        e = ("There was an error during execution: "
             "Environment variable {} doesn't seem to be "
             "specified in format 'KEY=VALUE'.".format(la_la_la))
        assert e in exc.value.message


def test_build_basic_image_with_labels():
    a_b = "A=B"
    x_y = "x=y"
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", "-l", a_b, x_y, "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd)
    out = inspect_buildah_resource("image", target_image)
    assert out["OCIv1"]["config"]["Labels"]["A"] == "B"
    assert out["OCIv1"]["config"]["Labels"]["x"] == "y"
    buildah("rmi", [target_image])


def test_build_basic_image_with_build_volumes(tmpdir):
    real_tmp = str(tmpdir)
    with open(os.path.join(real_tmp, "file.txt"), "w") as fd:
        fd.write("Hello, hello!")
    container_mount = "/asdqwe"
    vol_spec = "%s:%s" % (real_tmp, container_mount)
    basic_playbook_path = os.path.join(data_dir, "basic_playbook_with_volume.yaml")
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", "--build-volumes", vol_spec, "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd)
    buildah("rmi", [target_image])


def test_build_basic_image_with_all_params(tmpdir):
    workdir_path = "/etc"
    l_a_b = "A=B"
    l_x_y = "x=y"
    e_a_b = "A=B"
    e_x_y = "X=Y"
    cmd, cmd_e = "ls -lha", ["ls", "-lha"]
    user = "1000123"
    p_80, p_443 = "80", "443"
    runtime_volume = "/var/lib/asdqwe"
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build",
           "-w", workdir_path,
           "-l", l_a_b, l_x_y,
           "-e", e_a_b, e_x_y,
           "--cmd", cmd,
           "-u", user,
           "-p", p_80, p_443,
           "--runtime-volumes", runtime_volume,
           "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd)
    try:
        out = inspect_buildah_resource("image", target_image)
        co = out["OCIv1"]["config"]
        assert co["WorkingDir"] == workdir_path
        assert co["Labels"]["A"] == "B"
        assert co["Labels"]["x"] == "y"
        assert e_a_b in co["Env"]
        assert e_x_y in co["Env"]
        assert co["Cmd"] == cmd_e
        assert co["User"] == user
        assert p_80 in co["ExposedPorts"]
        assert p_443 in co["ExposedPorts"]
        # assert runtime_volume in co["Volumes"]  # FIXME: figure out how to check this
    finally:
        buildah("rmi", [target_image])


def test_build_failure():
    bad_playbook_path = os.path.join(data_dir, "bad_playbook.yaml")
    base_image = "docker.io/library/python:3-alpine"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    target_failed_image = target_image + "-failed"
    cmd = ["build", bad_playbook_path, base_image, target_image]
    with pytest.raises(subprocess.CalledProcessError):
        ab(cmd)
    buildah("inspect", ["-t", "image", target_failed_image])
    buildah("rmi", [target_failed_image])


def test_two_runs():
    """ run ab twice and see if the other instance fails """
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    base_image = "docker.io/library/python:3-alpine"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["python3", "-m", "ansible_bender.cli", "build", basic_playbook_path, base_image, target_image]
    p1 = subprocess.Popen(cmd)
    p2 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p2.communicate()
    assert "ab is already running" in err.decode("utf-8")
    p1.wait()

