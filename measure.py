from yaml import dump
import Levenshtein
from os import path
from subprocess import PIPE, Popen, STDOUT
from sys import stderr
from tempfile import TemporaryDirectory


def get_num_deleted_lines(source_filename, formatted_source):
    diff_args = ["diff", "--changed-group-format='%<'", "--unchanged-group-format=''", source_filename, "-"]
    # diff_args = ["wc", "-c", "-"]
    p = Popen(diff_args, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    diff_output = str(p.communicate(input=str.encode(formatted_source))[0])
    return diff_output.count('\n')


def measure_file(source_filename, workspace_path, command):
    with open(source_filename) as source_file:
        source = source_file.read()

    clang_format_args = [command, "-style=file", "-"]
    p = Popen(clang_format_args, stdout=PIPE, stdin=PIPE, stderr=STDOUT, cwd=workspace_path)
    formatted_source = str(p.communicate(input=str.encode(source))[0])

    num_deleted_lines = get_num_deleted_lines(source_filename, formatted_source)
    edit_distance = Levenshtein.distance(source, formatted_source)

    return (num_deleted_lines, edit_distance)


def measure(config, source_filenames, args):
    with TemporaryDirectory() as workspace_path:
        config_filename = path.join(workspace_path, ".clang-format")
        with open(config_filename, "wt") as config_file:
            config_file.write(dump(config))

        scores = [measure_file(source_filename, workspace_path, args.command) for source_filename in source_filenames]
        num_deleted_lines, edit_distance = [sum(score) for score in zip(*scores)]

        print('.', end='', file=stderr, flush=True)

        return (num_deleted_lines, edit_distance)
