"""
CLI for ansible builder
"""

import argparse
import logging
import sys

from ansible_bender.api import Application
from ansible_bender.builders.base import ImageMetadata
from ansible_bender.constants import OUT_LOGGER_FORMAT, OUT_LOGGER


def set_logging(
        logger_name="ab",
        level=logging.INFO,
        handler_class=logging.StreamHandler,
        handler_kwargs=None,
        format='%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s',
        date_format='%H:%M:%S'):
    """
    Set personal logger for this library.

    :param logger_name: str, name of the logger
    :param level: int, see logging.{DEBUG,INFO,ERROR,...}: level of logger and handler
    :param handler_class: logging.Handler instance, default is StreamHandler (/dev/stderr)
    :param handler_kwargs: dict, keyword arguments to handler's constructor
    :param format: str, formatting style
    :param date_format: str, date style in the logs
    :return: logger instance
    """
    logger = logging.getLogger(logger_name)
    # do we want to propagate to root logger?
    # logger.propagate = False
    logger.setLevel(level)

    # don't readd handler
    if not [x for x in logger.handlers if isinstance(x, handler_class)]:
        handler_kwargs = handler_kwargs or {}
        handler = handler_class(**handler_kwargs)
        handler.setLevel(level)
        formatter = logging.Formatter(format, date_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


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
        return strink.split(pattern, 1)
    except ValueError:
        raise RuntimeError(error_message)


class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='ab',
            description='Ansible builder = ansible-playbook + {buildah,docker}  '
                        '# create your container images with Ansible! ',
            epilog="Please use '--' to separate options and arguments."
        )
        self.parser.add_argument("-v", "--verbose", action="store_true",
                                 help="provide verbose output")
        self.parser.add_argument("--debug", action="store_true",
                                 help="provide all the output")
        subparsers = self.parser.add_subparsers( help='commands')
        self.build_parser = subparsers.add_parser(
            name="build",
            epilog="Please use '--' to separate options and arguments."
        )
        self.build_parser.add_argument(
            "playbook_path", metavar="PLAYBOOK_PATH",
            help="path to Ansible playbook"
        )
        self.build_parser.add_argument(
            "base_image", metavar="BASE_IMAGE",
            help="name of a container image to use as a base"
        )
        self.build_parser.add_argument(
            "target_image", metavar="TARGET_IMAGE",
            help="name of the built container image"
        )
        self.build_parser.add_argument("--builder", help="pick preferred builder backend",
                                       default="buildah",
                                       choices=["docker", "buildah"])
        self.build_parser.add_argument(
            "--build-volumes",
            help="mount selected directory inside the container during build, "
                 "should be specified as '/host/dir:/container/dir'",
            nargs="*"
        )
        self.build_parser.add_argument(
            "-w", "--workdir",
            help="path to an implicit working directory in the container"
        )
        self.build_parser.add_argument(
            "-l", "--labels",
            help="add a label to the metadata of the image, "
                 "should be specified as 'key=value'",
            nargs="*"
        )
        # docker allows -e KEY and it is inherited from the current env
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
            help="path a directory which has daata stored outside of the container",
            nargs="*"
        )
        self.build_parser.set_defaults(subcommand="build")
        self.args = self.parser.parse_args()
        if self.args.debug:
            set_logging(level=logging.DEBUG)
        elif self.args.verbose:
            set_logging(level=logging.INFO)
            set_logging(logger_name=OUT_LOGGER, level=logging.INFO, format=OUT_LOGGER_FORMAT)
        else:
            set_logging(level=logging.WARNING)
            set_logging(logger_name=OUT_LOGGER, level=logging.INFO, format=OUT_LOGGER_FORMAT)

    def _build(self):
        metadata = ImageMetadata()
        if self.args.workdir:
            metadata.working_dir = self.args.workdir
        if self.args.labels:
            for label in self.args.labels:
                err_msg = "Label variable {} doesn't seem to be " + \
                          "specified in format 'KEY=VALUE'.".format(label)
                k, v = split_once_or_fail_with(label, "=", err_msg)
                metadata.labels[k] = v
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
        app = Application(
            self.args.playbook_path, self.args.base_image, self.args.target_image,
            self.args.builder, metadata, debug=self.args.debug
        )
        app.build(build_volumes=self.args.build_volumes)

    def run(self):
        subcommand = getattr(self.args, "subcommand", "nope")
        try:
            if subcommand == "build":
                self._build()
                return 0
        except KeyboardInterrupt:
            return 133
        except Exception as ex:
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
