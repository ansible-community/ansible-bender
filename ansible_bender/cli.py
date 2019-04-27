"""
CLI for ansible builder
"""

import argparse
import json
import sys

import yaml
from tabulate import tabulate

from ansible_bender.api import Application
from ansible_bender.constants import ANNOTATIONS_KEY
from ansible_bender.core import PbVarsParser
from ansible_bender.db import PATH_CANDIDATES
from ansible_bender.okd import build_inside_openshift


def split_once_or_fail_with(strink, pattern, error_message):
    """
    split selected string (string is a builtin, hence strink) using the given pattern;
    raise RuntimeError with provided error message if that fails

    :param strink: str, string to split
    :param pattern: str, pattern to split on
    :param error_message: str, error message to raise in case of split fails
    :return: (str, str)
    """
    try:
        k, v = strink.split(pattern, 1)
    except ValueError:
        raise RuntimeError(error_message)
    # we do this on purpose, so that ValueError is raised here
    return k, v


class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='ansible-bender',
            description='Ansible builder = ansible-playbook + {buildah,docker}  '
                        '# create your container images with Ansible! ',
            epilog="Please use '--' to separate options and arguments."
        )
        self.parser.add_argument("-v", "--verbose", action="store_true",
                                 help="provide verbose output")
        self.parser.add_argument("--debug", action="store_true",
                                 help="provide all the output")
        candidates_str = ", ".join(filter(lambda x: x, PATH_CANDIDATES))
        self.parser.add_argument(
            "--database-dir",
            action="store",
            help="a path to directory where ab will store runtime data, defaults to: \"%s\""
                 % candidates_str
        )
        self.subparsers = self.parser.add_subparsers(help='commands')

        self._do_build_interface()
        self._do_list_builds_interface()
        self._do_get_logs_interface()
        self._do_inspect_interface()
        self._do_push_interface()

        self.args = self.parser.parse_args()
        debug = False
        if self.args.debug:
            debug = True
        verbose = False
        if self.args.verbose:
            verbose = True
        self.app = Application(debug=debug, db_path=self.args.database_dir, verbose=verbose)

    def _do_build_interface(self):
        self.build_parser = self.subparsers.add_parser(
            name="build",
            epilog="Please use '--' to separate options and arguments."
        )
        self.build_parser.add_argument(
            "playbook_path", metavar="PLAYBOOK_PATH",
            help="path to Ansible playbook"
        )
        self.build_parser.add_argument(
            "base_image", metavar="BASE_IMAGE",
            help="name of a container image to use as a base",
            nargs="?"
        )
        self.build_parser.add_argument(
            "target_image", metavar="TARGET_IMAGE",
            help="name of the built container image",
            nargs="?"
        )
        self.build_parser.add_argument("--builder", help="pick preferred builder backend",
                                       default="buildah",
                                       choices=["docker", "buildah"])
        self.build_parser.add_argument(
            "--no-cache",
            action="store_true",
            default=None,
            help="disable caching mechanism: storing layers and loading them if a task is unchanged; "
                 "this option also implies the final image is composed of a base image and one additional layer"
        )
        self.build_parser.add_argument(
            "--build-volumes",
            help="mount selected directory inside the container during build, "
                 "should be specified as '/host/dir:/container/dir'",
            nargs="*"
        )
        self.build_parser.add_argument(
            "--build-user",
            help="the container gets invoked with this user during build"
        )
        self.build_parser.add_argument(
            "-w", "--workdir",
            help="path to an implicit working directory in the container"
        )
        self.build_parser.add_argument(
            "-l", "--label",
            help="add a label to the metadata of the image, "
                 "should be specified as 'key=value'",
            nargs="*",
            dest="labels"
        )
        self.build_parser.add_argument(
            "--annotation",
            help="Add key=value annotation for the target image",
            nargs="*",
            dest=ANNOTATIONS_KEY
        )
        # TODO: docker allows -e KEY and it is inherited from the current env
        self.build_parser.add_argument(
            "-e", "--env-vars",
            help="add an environment variable to the metadata of the image, "
                 "should be specified as 'KEY=VALUE'",
            nargs="*"
        )
        self.build_parser.add_argument(
            "--cmd",
            help="command to run by default in the container"
        )
        self.build_parser.add_argument(
            "-u", "--user",
            help="the container gets invoked with this user by default"
        )
        self.build_parser.add_argument(
            "-p", "--ports",
            help="ports to expose from container by default",
            nargs="*"
        )
        self.build_parser.add_argument(
            "--runtime-volumes",
            help="path a directory which has data stored outside of the container",
            nargs="*"
        )
        self.build_parser.add_argument(
            "--extra-ansible-args",
            help="arguments passed to ansible-playbook command (be careful!)"
        )
        self.build_parser.add_argument(
            "--python-interpreter",
            help="Path to a python interpreter inside the base image"
        )
        self.build_parser.set_defaults(subcommand="build")

        self.bio_parser = self.subparsers.add_parser(
            name="build-inside-openshift",
            description="Build image within an openshift environment.",
        )
        self.bio_parser.set_defaults(subcommand="bio")

    def _do_get_logs_interface(self):
        self.gl_parser = self.subparsers.add_parser(
            name="get-logs",
            description="show logs of a specific build (default to latest build)",
        )
        self.gl_parser.add_argument(
            "BUILD_ID",
            help="ID of the build",
            nargs="?",
            default=None
        )
        self.gl_parser.set_defaults(subcommand="get-logs")

    def _do_list_builds_interface(self):
        self.lb_parser = self.subparsers.add_parser(
            name="list-builds",
            description="print a list of past and present builds",
        )
        self.lb_parser.set_defaults(subcommand="list-builds")

    def _do_inspect_interface(self):
        self.inspect_parser = self.subparsers.add_parser(
            name="inspect",
            description="provide detailed information for a selected build (default to latest build)",
        )
        self.inspect_parser.add_argument(
            "BUILD_ID",
            help="ID of the build",
            nargs="?",
            default=None
        )
        self.inspect_parser.add_argument(
            "--json",
            help="output the information in JSON format",
            action="store_true"
        )
        self.inspect_parser.set_defaults(subcommand="inspect")

    def _do_push_interface(self):
        self.push_parser = self.subparsers.add_parser(
            name="push",
            description="push built image to a different location (default to latest build)",
            epilog="This command is thin wrapper on top of `podman push` command. "
                   "The target is passed directly to podman, for more information, please consult "
                   " podman-push(1) manpage or skopeo(1)."
        )
        self.push_parser.add_argument(
            "TARGET",
            help="Target is composed of \"transport:details\"",
            default=None
        )
        self.push_parser.add_argument(
            "BUILD_ID",
            help="ID of the build",
            nargs="?",
            default=None
        )
        # nothing to force so far
        # self.push_parser.add_argument(
        #     "--force",
        #     help="Bypass any checks and just go for it",
        #     action="store_true"
        # )
        self.push_parser.set_defaults(subcommand="push")

    def _build(self):
        pb_vars_p = PbVarsParser(self.args.playbook_path)
        build, metadata = pb_vars_p.get_build_and_metadata()
        build.metadata = metadata
        if self.args.workdir:
            metadata.working_dir = self.args.workdir
        if self.args.labels:
            for label in self.args.labels:
                err_msg = "Label variable {} doesn't seem to be " + \
                          "specified in format 'KEY=VALUE'.".format(label)
                k, v = split_once_or_fail_with(label, "=", err_msg)
                metadata.labels[k] = v
        if self.args.annotations:
            for ann in self.args.annotations:
                err_msg = "Annotation {} doesn't seem to be " + \
                          "specified in format 'KEY=VALUE'.".format(ann)
                k, v = split_once_or_fail_with(ann, "=", err_msg)
                metadata.annotations[k] = v
        if self.args.env_vars:
            for e_v in self.args.env_vars:
                err_msg = "Environment variable {} doesn't seem to be " + \
                    "specified in format 'KEY=VALUE'.".format(e_v)
                k, v = split_once_or_fail_with(e_v, "=", err_msg)
                metadata.env_vars[k] = v
        if self.args.cmd:
            metadata.cmd = self.args.cmd
        if self.args.user:
            metadata.user = self.args.user
        if self.args.ports:
            metadata.ports = self.args.ports
        if self.args.runtime_volumes:
            metadata.volumes = self.args.runtime_volumes

        build.playbook_path = self.args.playbook_path
        if self.args.build_volumes:
            build.build_volumes = self.args.build_volumes
        if self.args.base_image:
            build.base_image = self.args.base_image
        if self.args.target_image:
            build.target_image = self.args.target_image
        if self.args.builder:
            build.builder_name = self.args.builder
        if self.args.no_cache is not None:
            build.cache_tasks = not self.args.no_cache
        if self.args.extra_ansible_args:
            build.ansible_extra_args = self.args.extra_ansible_args
        if self.args.python_interpreter:
            build.python_interpreter = self.args.python_interpreter

        self.app.build(build)

    def _build_inside_openshift(self):
        build_inside_openshift(self.app)

    def _list_builds(self):
        builds = self.app.list_builds()
        header = ("BUILD ID", "IMAGE NAME", "STATUS", "DATE", "BUILD TIME")
        builds_data = []
        for b in builds:
            build_time = ""
            if b.build_finished_time and b.build_start_time:
                build_time = b.build_finished_time - b.build_start_time
            builds_data.append((
                b.build_id,
                b.target_image,
                b.state.value,
                b.build_finished_time if b.build_finished_time else "",
                build_time  # TODO: make it fancy
            ))
        print(tabulate(builds_data, headers=header))

    def _get_logs(self):
        build_id = self.args.BUILD_ID
        log_lines = self.app.get_logs(build_id=build_id)
        print("\n".join(log_lines))

    def _inspect(self):
        build_id = self.args.BUILD_ID
        inspect_data = self.app.inspect(build_id=build_id)
        if self.args.json:
            print(json.dumps(inspect_data))
        else:
            yaml.safe_dump(inspect_data, sys.stdout, indent=2, default_flow_style=False)

    def _push(self):
        build_id = self.args.BUILD_ID
        target = self.args.TARGET
        # force = self.args.force
        self.app.push(target, build_id=build_id, force=False)

    def run(self):
        subcommand = getattr(self.args, "subcommand", "nope")
        try:
            if subcommand == "build":
                self._build()
                return 0
            elif subcommand == "list-builds":
                self._list_builds()
                return 0
            elif subcommand == "get-logs":
                self._get_logs()
                return 0
            elif subcommand == "inspect":
                self._inspect()
                return 0
            elif subcommand == "push":
                self._push()
                return 0
            elif subcommand == "bio":
                self._build_inside_openshift()
                return 0
        except KeyboardInterrupt:
            return 133
        except Exception as ex:
            self.app.clean()
            stderr = getattr(ex, "stderr", "")
            if stderr:
                print(stderr, file=sys.stderr)
            if self.args.debug:
                raise
            print("There was an error during execution: %s" % ex, file=sys.stderr)
            return 2
        self.parser.print_help()
        return 1


def main():
    sys.exit(CLI().run())


if __name__ == '__main__':
    main()
