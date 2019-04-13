import os
import random
import string


tests_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(tests_dir)
data_dir = os.path.abspath(os.path.join(tests_dir, "data"))
roles_dir = os.path.join(data_dir, "roles")
buildah_inspect_data_path = os.path.join(data_dir, "buildah_inspect.json")
basic_playbook_path = os.path.join(data_dir, "basic_playbook.yaml")
multiplay_path = os.path.join(data_dir, "multiplay.yaml")
non_ex_pb = os.path.join(data_dir, "non_ex_pb.yaml")
b_p_w_vars_path = os.path.join(data_dir, "b_p_w_vars.yaml")
p_w_vars_files_path = os.path.join(data_dir, "p_w_vars_files.yaml")
full_conf_pb_path = os.path.join(data_dir, "full_conf_pb.yaml")
basic_playbook_path_w_bv = os.path.join(data_dir, "basic_playbook_with_volume.yaml")
dont_cache_playbook_path_pre = os.path.join(data_dir, "dont_cache_playbook_pre.yaml")
dont_cache_playbook_path = os.path.join(data_dir, "dont_cache_playbook.yaml")
small_basic_playbook_path = os.path.join(data_dir, "small_basic_playbook.yaml")
change_layering_playbook = os.path.join(data_dir, "change_layering.yaml")
bad_playbook_path = os.path.join(data_dir, "bad_playbook.yaml")
role_pb_path = os.path.join(data_dir, "role.yaml")
base_image = "docker.io/library/python:3-alpine"

C7_AP_VER_OUT = """\
ansible-playbook 2.4.2.0
  config file = /etc/ansible/ansible.cfg
  configured module search path = [u'/root/.ansible/plugins/modules', u'/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python2.7/site-packages/ansible
  executable location = /usr/bin/ansible-playbook
  python version = 2.7.5 (default, Oct 30 2018, 23:45:53) [GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]
"""


def random_word(length):
    # https://stackoverflow.com/a/2030081/909579
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))
