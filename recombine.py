from random import choice, random, randrange
from sys import stderr


def make_choice(*choices):
    return lambda value, mutation_rate: choice(choices)


def make_delta_sq(factor, minimum=0):
    return lambda value, mutation_rate: max(minimum,
                                            int(value) + randrange(-factor, factor + 1) * randrange(factor + 1))


def make_range(start, stop):
    return lambda value, mutation_rate: randrange(start, stop)


mutation_rules = {
    "BasedOnStyle": make_choice("LLVM", "Google", "Chromium", "Mozilla", "WebKit"),
    "DisableFormat": lambda value, mutation_rate: False,
    "AllowShortFunctionsOnASingleLine": make_choice("None", "Empty", "Inline", "All"),
    "ConstructorInitializerIndentWidth": make_delta_sq(4),
    "PenaltyBreakFirstLessLess": make_delta_sq(10),
    "MacroBlockEnd": lambda value, mutation_rate: value,
    "MacroBlockBegin": lambda value, mutation_rate: value,
    "IncludeCategories": lambda value, mutation_rate: [mutate(item, mutation_rate) for item in value],
    "    Priority": make_range(1, 4),
    "AlignAfterOpenBracket": make_choice("Align", "DontAlign", "AlwaysBreak"),
    "AlwaysBreakAfterReturnType": make_choice("None", "All", "TopLevel", "AllDefinitions", "TopLevelDefinitions"),
    "AccessModifierOffset": make_range(-8, 9),
    "BreakBeforeBraces": make_choice("Attach", "Linux", "Mozilla", "Stroustrup", "Allman", "GNU", "WebKit", "Custom"),
    "PenaltyBreakComment": make_delta_sq(10),
    "PenaltyExcessCharacter": make_delta_sq(1000),
    "ObjCBlockIndentWidth": make_range(0, 8),
    "IncludeIsMainRegex": lambda value, mutation_rate: value,
    "PointerAlignment": make_choice("Left", "Right", "Middle"),
    "ForEachMacros": lambda value, mutation_rate: value,
    "BraceWrapping": lambda value, mutation_rate: mutate(value, mutation_rate),
    "  - Regex": lambda value, mutation_rate: value,
    "PenaltyReturnTypeOnItsOwnLine": make_delta_sq(10),
    "PenaltyBreakString": make_delta_sq(25),
    "ColumnLimit": make_delta_sq(5, 1),
    "TabWidth": make_delta_sq(3),
    "IndentWidth": make_delta_sq(4),
    "SpaceBeforeParens": make_choice("Never", "ControlStatements", "Always"),
    "Standard": make_choice("Cpp03", "Cpp11", "Auto"),
    "UseTab": make_choice("Never", "ForIndentation", "Always"),
    "Language": make_choice("None", "Cpp", "Java", "JavaScript", "Proto", "TableGen"),
    "BreakBeforeBinaryOperators": make_choice("None", "NonAssignment", "All"),
    "JavaScriptQuotes": make_choice("Leave", "Single", "Double"),
    "PenaltyBreakBeforeFirstCallParameter": make_delta_sq(2),
    "AlwaysBreakAfterDefinitionReturnType": make_choice("None", "All", "TopLevel"),
    "MaxEmptyLinesToKeep": make_delta_sq(1),
    "SpacesBeforeTrailingComments": make_delta_sq(3),
    "NamespaceIndentation": make_choice("None", "Inner", "All"),
    "ContinuationIndentWidth": make_delta_sq(3),
    "CommentPragmas": lambda value, mutation_rate: value,
    "Priority": lambda value, mutation_rate: value,
    "Regex": lambda value, mutation_rate: value,
    "PenaltyBreakAssignment": make_delta_sq(2),
    "AlignEscapedNewlines": make_choice("DontAlign", "Left", "Right"),
    "BreakConstructorInitializers": make_choice("BeforeColon", "BeforeComma", "AfterColon"),
}


def mutate_value(key, value, mutation_rate):
    if key in mutation_rules:
        mutation_rule = mutation_rules[key]
        return mutation_rule(value, mutation_rate)

    if isinstance(value, bool):
        return not value

    print("Unrecognized setting, '{}: {}', in .clang-format configuration.".format(key, value), file=stderr)
    return value


def visit_line(key, value, mutation_rate):
    return mutate_value(key, value, mutation_rate) if random() < mutation_rate else value


def mutate(config, mutation_rate):
    return {key: visit_line(key, value, mutation_rate) for key, value in config.items()}


def recombine(scored_parents, args):
    ranked = sorted(scored_parents, key=lambda scored_parent: scored_parent[0])

    fittest = ranked[0]
    (fittest_score, fittest_config) = fittest

    # rank-based selection with elitism
    elite_configs = [fittest_config]
    recombined_configs = [mutate(ranked[int(random() * random() * len(ranked))][1], args.mutation) for _ in
                          range(args.population - 1)]
    recombination = elite_configs + recombined_configs

    return (fittest, recombination)
