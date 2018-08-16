"""
Make sure that we can build using buildah builder.
"""
import os
import random
import string
import subprocess

import pytest

from ab.builders.buildah_builder import buildah, inspect_buildah_resource

this_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(this_dir))
data_dir = os.path.join(this_dir, "data")


def random_word(length):
    # https://stackoverflow.com/a/2030081/909579
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def ab(args):
    """
    python3 -m ab.cli -v build ./playbook.yaml registry.fedoraproject.org/fedora:28 asdqwe-image

    :return:
    """
    cmd = ["python3", "-m", "ab.cli"]
    subprocess.check_call(cmd + args, cwd=project_dir)


def test_build_basic_image():
    basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
    # TODO: pick smaller image: python3 & alpine
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", basic_playbook_path, base_image, target_image]
    ab(cmd)
    buildah("inspect", ["-t", "image", "localhost/ddbd:latest"])
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
    # TODO: also run container and make sure that the env var is set inside the container
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
    cmd = ["build", "-v", vol_spec, "--",
           basic_playbook_path, base_image, target_image]
    ab(cmd)
    buildah("rmi", [target_image])
