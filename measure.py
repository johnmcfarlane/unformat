from functools import lru_cache
import Levenshtein
from os import path
from shlex import quote, split
from subprocess import PIPE, Popen, STDOUT
from sys import stderr
from tempfile import TemporaryDirectory


class FormatterError(Exception):
    pass


class FormatterCrash(Exception):
    pass


def get_num_deleted_lines(source_filename, formatted_source):
    diff_args = ["diff", "--changed-group-format='%<'", "--unchanged-group-format=''", source_filename, "-"]
    # diff_args = ["wc", "-c", "-"]
    p = Popen(diff_args, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    diff_output = p.communicate(input=str.encode(formatted_source))[0].decode("utf-8")
    return diff_output.count('\n')


@lru_cache(maxsize=4096)
def invoke_formatter(command_line, source_filename, config_filename, workspace_path, debug):
    with open(source_filename) as source_file:
        source = source_file.read()

    popenargs = split(command_line)
    p = Popen(popenargs, stdout=PIPE, stdin=PIPE, stderr=STDOUT, cwd=workspace_path)
    output = p.communicate(input=str.encode(source))
    formatted_source = output[0].decode("utf-8")

    if p.returncode:
        if debug:
            print("\nError code returned: {}".format(p.returncode), file=stderr)

            print("Command line: {}".format(popenargs), file=stderr)

            print("Error message:\n{}\nEOF".format(formatted_source), file=stderr)

            print("source:\n{}\nEOF".format(source), file=stderr)

            with open(config_filename) as config_file:
                config_buffer = config_file.read()
                print("config:\n{}\nEOF".format(config_buffer), file=stderr)

        raise FormatterCrash if p.returncode == -11 else FormatterError

    num_deleted_lines = get_num_deleted_lines(source_filename, formatted_source)
    edit_distance = Levenshtein.distance(source, formatted_source)

    return (edit_distance, num_deleted_lines)


def measure_file(source_filename, config_filename, workspace_path, args):
    popenargs = args.backend.format_args(args, source_filename)

    command_line = ' '.join(quote(arg) for arg in popenargs)

    return invoke_formatter(command_line, source_filename, config_filename, workspace_path, args.debug)


def measure(config, source_filenames, args):
    with TemporaryDirectory() as workspace_path:
        config_filename = path.join(workspace_path, args.backend.default_config_filename())
        with open(config_filename, "wt") as config_file:
            config_file.write(args.backend.encode(config))

        try:
            scores = [measure_file(source_filename, config_filename, workspace_path, args) for source_filename in source_filenames]

            num_deleted_lines, edit_distance = [sum(score) for score in zip(*scores)]
            scores = (num_deleted_lines, edit_distance)
            print('.', end='', file=stderr, flush=True)
        except FormatterError:
            scores = None
            print('?', end='', file=stderr, flush=True)
        except FormatterCrash:
            scores = None
            print('!', end='', file=stderr, flush=True)

        return scores
