"""
CLI for ansible builder
"""

import argparse
import logging
import sys

from ab.api import Application
from ab.builder import ImageMetadata


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


class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='ab',
            description='Ansible builder = ansible-playbook + {buildah,docker}  '
                        '# create your container images with Ansible! ',
            epilog="Please use '--' to separate options and arguments."
        )
        self.parser.add_argument("-v", "--verbose", action="store_true",
                                 help="run verbosely, also print possible tracebacks")
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
        # docker allows -e KEY and it is inherited from the current env
        self.build_parser.add_argument(
            "-e", "--env-var",
            help="add an environment variable to the metadata of the image, "
                 "should be specified as 'KEY=VALUE'",
            nargs="*"
        )
        self.build_parser.add_argument(
            "-l", "--label",
            help="add a label to the metadata of the image, "
                 "should be specified as 'key=value'",
            nargs="*"
        )
        self.build_parser.set_defaults(subcommand="build")
        self.args = self.parser.parse_args()
        if self.args.verbose:
            set_logging(level=logging.DEBUG)
        else:
            set_logging(level=logging.INFO)

    def _build(self):
        metadata = ImageMetadata()
        if self.args.env_var:
            for e_v in self.args.env_var:
                try:
                    k, v = e_v.split("=", 1)
                except ValueError:
                    raise RuntimeError(
                        "Environment variable {} doesn't seem to be "
                        "specified in format 'KEY=VALUE'.".format(e_v))
                metadata.env_vars[k] = v
        if self.args.label:
            for label in self.args.label:
                try:
                    k, v = label.split("=", 1)
                except ValueError:
                    raise RuntimeError(
                        "Label variable {} doesn't seem to be "
                        "specified in format 'KEY=VALUE'.".format(label))
                metadata.labels[k] = v
        app = Application(
            self.args.playbook_path, self.args.base_image, self.args.target_image,
            self.args.builder, metadata
        )
        app.build()

    def run(self):
        subcommand = getattr(self.args, "subcommand", "nope")
        try:
            if subcommand == "build":
                self._build()
                return 0
        except KeyboardInterrupt:
            return 133
        except Exception as ex:
            print("There was an error during execution: %s" % ex, file=sys.stderr)
            return 2
        self.parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(CLI().run())
