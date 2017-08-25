from os import path
from subprocess import check_output, PIPE
from sys import stderr

from yaml import load, dump

CONFIG_FILENAME = ".clang-format"


def make_default_config(command, style):
    args = [command, "-dump-config"] + ["-style={}".format(style)] if style else []
    config_buffer = check_output(args, stderr=PIPE).decode('ascii')
    config = load(config_buffer)
    return config


def make_initial_configs(args):
    if args.initial:
        config_filepath = args.initial
        with open(config_filepath) as config_file:
            print("Using the provided configuration file, '{}'".format(args.initial), file=stderr)
            return [load(config_file.read())]
    elif args.initial is None and args.root:
        config_filepath = path.join(args.root, CONFIG_FILENAME)
        try:
            with open(config_filepath) as config_file:
                print("Using the configuration file from the provided root, '{}'".format(args.root))
                return [load(config_file.read())]
        except FileNotFoundError:
            pass

    styles = ["LLVM", "Google", "Chromium", "Mozilla", "WebKit"]
    print("Using default .clang-format selection: {}".format(styles), file=stderr)
    return [make_default_config(args.command, style) for style in styles]


def present_config(config, args, exiting):
    config_buffer = dump(config)
    if args.root:
        # If output is file, always write out results
        # because the same copy can be updated with latest and greatest.
        if not exiting:
            config_filepath = path.join(args.root, CONFIG_FILENAME)
            with open(config_filepath, "w") as config_file:
                config_file.write(config_buffer)
    else:
        # If output is stdout, only write out results once on exit
        # because otherwise, stdout contains multiple copies of config.
        if exiting:
            print(config_buffer)