"""
Make sure that we can build using buildah builder.
"""
import os
import random
import string
import subprocess

from ab.builder import buildah

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
    # TODO: make sure the image is present or pull it
    base_image = "registry.fedoraproject.org/fedora:28"
    target_image = "registry.example.com/ab-test-" + random_word(12) + ":oldest"
    cmd = ["build", basic_playbook_path, base_image, target_image]
    ab(cmd)
    buildah("inspect", ["-t", "image", "localhost/ddbd:latest"])
    buildah("rmi", [target_image])
