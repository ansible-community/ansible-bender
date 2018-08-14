"""
CLI for ansible builder
"""

import argparse
import logging
import sys

from ab.api import Application


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
        self.parser = argparse.ArgumentParser(prog='ab', description='ansible builder')
        self.parser.add_argument("-v", "--verbose", action="store_true")
        subparsers = self.parser.add_subparsers(help='commands')
        self.build_parser = subparsers.add_parser(name="build")
        self.build_parser.add_argument("playbook_path")
        self.build_parser.add_argument("base_image")
        self.build_parser.add_argument("target_image")
        self.build_parser.set_defaults(subcommand="build")
        self.args = self.parser.parse_args()
        if self.args.verbose:
            set_logging(level=logging.DEBUG)

    def run(self):
        subcommand = getattr(self.args, "subcommand", "nope")
        if subcommand == "build":
            app = Application(
                self.args.playbook_path, self.args.base_image, self.args.target_image)
            app.build()
            return 0
        self.parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(CLI().run())
