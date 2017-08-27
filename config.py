from os import path
from random import randrange, gauss
from subprocess import check_output, PIPE
from sys import stderr

from yaml import load, dump


def make_choice(*choices):
    def pick_something_else(value, _):
        rr = randrange(len(choices) - 1)
        value_index = choices.index(value)
        other_index = rr if rr < value_index else rr + 1
        choice = choices[other_index]

        assert (value != choice)
        return choice

    return pick_something_else


def make_delta_gauss(sd, minimum=0):
    def deltarize(value, _):
        value_int = int(value)

        for _ in range(100):
            mutated_value_float = max(minimum, value_int + gauss(0, sd))
            mutated_value_int = int(mutated_value_float+.5)
            mutated_value = str(mutated_value_int)
            if mutated_value != value:
                return mutated_value

        exit("Infinite loop suspected in make_delta_gauss({}, {}.".format(sd, minimum))

    return deltarize


def make_range(start, stop):
    return lambda value, args: randrange(start, stop)


def make_identity():
    return lambda value, args: value


class ClangFormatBackend:
    def __init__(self, _):
        pass

    @staticmethod
    def default_command():
        return "clang-format"

    @staticmethod
    def default_config_filename():
        return ".clang-format"

    @staticmethod
    def decode(config_buffer):
        return load(config_buffer)

    @staticmethod
    def encode(config):
        return dump(config)

    @staticmethod
    def make_default_config(command, style):
        popenargs = [command, "-dump-config"] + ["-style={}".format(style)] if style else []
        config_buffer = check_output(popenargs, stderr=PIPE).decode('utf-8')
        config = load(config_buffer)
        return config

    @staticmethod
    def make_default_configs(command):
        styles = ["LLVM", "Google", "Chromium", "Mozilla", "WebKit"]
        print("Using default .clang-format selection: {}".format(styles), file=stderr)
        return [ClangFormatBackend.make_default_config(command, style) for style in styles]

    @staticmethod
    def format_args(args, source_filename):
        return [
            args.command,
            "-style=file", "-",
            "-assume-filename={}".format(source_filename)]

    @staticmethod
    def mutation_rules(args, mutate):
        return {
            "BasedOnStyle": make_choice("LLVM", "Google", "Chromium", "Mozilla", "WebKit"),
            "DisableFormat": lambda value, args: False,
            "AllowShortFunctionsOnASingleLine": make_choice("None", "Empty", "Inline", "All"),
            "ConstructorInitializerIndentWidth": make_delta_gauss(4),
            "PenaltyBreakFirstLessLess": make_delta_gauss(10),
            "MacroBlockEnd": make_identity(),
            "MacroBlockBegin": make_identity(),
            "IncludeCategories": lambda value, args: [mutate(item, args) for item in value],
            "    Priority": make_range(1, 4),
            "AlignAfterOpenBracket": make_choice("Align", "DontAlign", "AlwaysBreak"),
            "AlwaysBreakAfterReturnType": make_choice("None", "All", "TopLevel", "AllDefinitions",
                                                      "TopLevelDefinitions"),
            "AccessModifierOffset": make_range(-8, 9),
            "BreakBeforeBraces": make_choice("Attach", "Linux", "Mozilla", "Stroustrup", "Allman", "GNU", "WebKit",
                                             "Custom"),
            "PenaltyBreakComment": make_delta_gauss(10),
            "PenaltyExcessCharacter": make_delta_gauss(1000),
            "ObjCBlockIndentWidth": make_range(0, 8),
            "IncludeIsMainRegex": make_identity(),
            "PointerAlignment": make_choice("Left", "Right", "Middle"),
            "ForEachMacros": make_identity(),
            "BraceWrapping": lambda value, args: mutate(value, args),
            "  - Regex": make_identity(),
            "PenaltyReturnTypeOnItsOwnLine": make_delta_gauss(10),
            "PenaltyBreakString": make_delta_gauss(25),
            "ColumnLimit": make_delta_gauss(5, 1),
            "TabWidth": make_delta_gauss(3),
            "IndentWidth": make_delta_gauss(4),
            "SpaceBeforeParens": make_choice("Never", "ControlStatements", "Always"),
            "Standard": make_choice("Cpp03", "Cpp11", "Auto"),
            "UseTab": make_choice("Never", "ForIndentation", "Always"),
            "Language": make_choice("None", "Cpp", "Java", "JavaScript", "Proto", "TableGen"),
            "BreakBeforeBinaryOperators": make_choice("None", "NonAssignment", "All"),
            "JavaScriptQuotes": make_choice("Leave", "Single", "Double"),
            "PenaltyBreakBeforeFirstCallParameter": make_delta_gauss(2),
            "AlwaysBreakAfterDefinitionReturnType": make_choice("None", "All", "TopLevel"),
            "MaxEmptyLinesToKeep": make_delta_gauss(1),
            "SpacesBeforeTrailingComments": make_delta_gauss(3),
            "NamespaceIndentation": make_choice("None", "Inner", "All"),
            "ContinuationIndentWidth": make_delta_gauss(3),
            "CommentPragmas": make_identity(),
            "Priority": make_identity(),
            "Regex": make_identity(),
        }


class UncrustifyBackend:
    @staticmethod
    def default_command():
        return "uncrustify"

    @staticmethod
    def default_config_filename():
        return ".uncrustify"

    @staticmethod
    def decode(config_buffer):
        lines = str.splitlines(config_buffer)
        uncommented_lines = [line for line in lines if not line.startswith('#')]
        pairs = [tuple(str.split(line, '=')) for line in uncommented_lines if '=' in line]
        config = {key.strip(): str(value.strip()) for key, value in pairs}

        if config["code_width"] == 0:
            config["code_width"] = 100

        return config

    @staticmethod
    def encode(config):
        uncommented_lines = sorted(["{} = {}".format(key, value) for key, value in config.items()])
        return '\n'.join(uncommented_lines)

    @staticmethod
    def make_default_configs(command):
        popenargs = [command, "--update-config"]
        config_buffer = check_output(popenargs, stderr=PIPE).decode('utf-8');
        config = UncrustifyBackend.decode(config_buffer)
        return [config]

    @staticmethod
    def format_args(args, source_filename):
        return [
            args.command,
            "-c", UncrustifyBackend.default_config_filename(),
            "--assume", source_filename]

    @staticmethod
    def make_mutation_rule_value(key, value_string):
        if value_string == "Unsigned Number":
            return make_delta_gauss(2, 0)
        elif value_string == "Number":
            return make_delta_gauss(2, 0)

        values = str.split(value_string, ' ')
        if values == ["String"]:
            return make_identity()
        elif values[0] == '{':
            assert (values[-1] == '}')
            choices = ''.join(values[1:-1]).split(',')
            return make_choice(*[choice.lower() for choice in choices])
        else:
            exit("Unrecognized value type, \"{}\" for key, \"{}\".".format(value_string, key))

    @staticmethod
    def parse_line(line):
        pos = line.find(' ')

        return (line[:pos], line[pos:].strip())

    @staticmethod
    def mutation_rules(args, mutate):
        popenargs = [args.command, "--show-config"]
        config_buffer = check_output(popenargs, stderr=PIPE).decode('utf-8')
        lines = str.splitlines(config_buffer)
        uncommented_lines = [line for line in lines if not (line.startswith('#') or line.startswith(' ') or not line)]
        parsed_lines = (UncrustifyBackend.parse_line(line) for line in uncommented_lines if ' ' in line)
        pairs = [(key, UncrustifyBackend.make_mutation_rule_value(key, value)) for key, value in parsed_lines]

        return {key: value for key, value in pairs}

    @staticmethod
    def sanitize(config):
        config["nl_max"] = '0'   # clashes with nl_max


def make_initial_configs(args):
    if args.initial:
        config_filepath = args.initial
        with open(config_filepath) as config_file:
            print("Using the provided configuration file, '{}'".format(args.initial), file=stderr)
            return [args.backend.decode(config_file.read())]
    elif args.initial is None and args.root:
        config_filepath = path.join(args.root, args.backend.default_config_filename())
        try:
            with open(config_filepath) as config_file:
                print("Using the configuration file, '{}', from the provided root, '{}'".format(config_filepath,
                                                                                                args.root))
                config_buffer = config_file.read()
                return [args.backend.decode(config_buffer)]
        except FileNotFoundError:
            pass

    return args.backend.make_default_configs(args.command)


def present_config(config, args, exiting):
    config_buffer = args.backend.encode(config)
    if args.root:
        # If output is file, always write out results
        # because the same copy can be updated with latest and greatest.
        if not exiting:
            config_filepath = path.join(args.root, args.backend.default_config_filename())
            try:
                with open(config_filepath, "w") as config_file:
                    config_file.write(config_buffer)
            except Exception as e:
                exit("Saving config file to project root, {}.\n{}".format(args.root, e))
    else:
        # If output is stdout, only write out results once on exit
        # because otherwise, stdout contains multiple copies of config.
        if exiting:
            print(config_buffer)
