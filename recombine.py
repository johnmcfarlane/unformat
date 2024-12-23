from random import choice, random, randrange
from sys import stderr


class _Mutator:
    """Mutates the contents of a config."""

    def __init__(self, mutation, locked_keys):
        self.mutation_rate = mutation
        self.locked_keys = locked_keys

    def mutate(self, config):
        return {key: self._visit_line(key, value) for key, value in config.items()}

    def _mutate_value(self, key, value):
        if key in mutation_rules:
            mutation_rule = mutation_rules[key]
            return mutation_rule(self, value)

        if isinstance(value, bool):
            return not value

        print("Unrecognized setting, '{}: {}', in .clang-format configuration.".format(key, value), file=stderr)
        return value

    def _visit_line(self, key, value):
        if key in self.locked_keys:
            return value

        return self._mutate_value(key, value) if random() < self.mutation_rate else value


def make_choice(*choices):
    return lambda _, value: choice(choices)


def make_delta_sq(factor, minimum=0):
    return lambda _, value: max(minimum, int(value) + randrange(-factor, factor + 1) * randrange(factor + 1))


def make_range(start, stop):
    return lambda _, value: randrange(start, stop)


mutation_rules = {
    "BasedOnStyle": make_choice("LLVM", "Google", "Chromium", "Mozilla", "WebKit"),
    "DisableFormat": lambda _m, _value: False,
    "AllowShortFunctionsOnASingleLine": make_choice("None", "Empty", "Inline", "All"),
    "ConstructorInitializerIndentWidth": make_delta_sq(4),
    "PenaltyBreakFirstLessLess": make_delta_sq(10),
    "MacroBlockEnd": lambda _m, value: value,
    "MacroBlockBegin": lambda _m, value: value,
    "IncludeCategories": lambda m, value: [m.mutate(item) for item in value],
    "    Priority": make_range(1, 4),
    "AlignAfterOpenBracket": make_choice("Align", "DontAlign", "AlwaysBreak"),
    "AlwaysBreakAfterReturnType": make_choice("None", "All", "TopLevel", "AllDefinitions", "TopLevelDefinitions"),
    "AccessModifierOffset": make_range(-8, 9),
    "BreakBeforeBraces": make_choice("Attach", "Linux", "Mozilla", "Stroustrup", "Allman", "GNU", "WebKit", "Custom"),
    "PenaltyBreakComment": make_delta_sq(10),
    "PenaltyExcessCharacter": make_delta_sq(1000),
    "ObjCBlockIndentWidth": make_range(0, 8),
    "IncludeIsMainRegex": lambda _m, value: value,
    "PointerAlignment": make_choice("Left", "Right", "Middle"),
    "ForEachMacros": lambda _m, value: value,
    "BraceWrapping": lambda m, value: m.mutate(value),
    "  - Regex": lambda _m, value: value,
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
    "CommentPragmas": lambda _m, value: value,
    "Priority": lambda _m, value: value,
    "Regex": lambda _m, value: value,
    "PenaltyBreakAssignment": make_delta_sq(2),
    "AlignEscapedNewlines": make_choice("DontAlign", "Left", "Right"),
    "AlignConsecutiveAssignments": make_choice("None", "Consecutive", "AcrossEmptyLines", "AcrossComments", "AcrossEmptyLinesAndComments"),
    "AlignConsecutiveBitFields": make_choice("None", "Consecutive", "AcrossEmptyLines", "AcrossComments", "AcrossEmptyLinesAndComments"),
    "AlignConsecutiveDeclarations": make_choice("None", "Consecutive", "AcrossEmptyLines", "AcrossComments", "AcrossEmptyLinesAndComments"),
    "AlignConsecutiveMacros": make_choice("None", "Consecutive", "AcrossEmptyLines", "AcrossComments", "AcrossEmptyLinesAndComments"),
    "AlignOperands": make_choice("DontAlign", "Align", "AlignAfterOperator"),
    "AllowShortBlocksOnASingleLine": make_choice("Never", "Empty", "Always"),
    "AllowShortIfStatementsOnASingleLine": make_choice("Never", "WithoutElse", "OnlyFirstIf", "AllIfsAndElse"),
    "AllowShortLambdasOnASingleLine": make_choice("None", "Empty", "Inline", "All"),
    "BitFieldColonSpacing": make_choice("Both", "None", "Before", "After"),
    "BreakConstructorInitializers": make_choice("BeforeColon", "BeforeComma", "AfterColon"),
    "BreakInheritanceList": make_choice("BeforeColon", "BeforeComma", "AfterColon", "AfterComma"),
    "EmptyLineBeforeAccessModifier": make_choice("Never", "Leave", "Always"),
    "IncludeBlocks": make_choice("Preserve", "Merge", "Regroup"),
    "IndentExternBlock": make_choice("AfterExternBlock", "NoIndent", "Indent"),
    "IndentPPDirectives": make_choice("None", "AfterHash", "BeforeHash"),
    "SpaceAroundPointerQualifiers": make_choice("Default", "Before", "After", "Both"),
}


def recombine(scored_parents, args):
    ranked = sorted(scored_parents, key=lambda scored_parent: scored_parent[0])

    fittest = ranked[0]
    (fittest_score, fittest_config) = fittest

    # rank-based selection with elitism
    elite_configs = [fittest_config]
    locked_keys = set(args.lock)

    mutator = _Mutator(args.mutation, locked_keys)

    recombined_configs = [mutator.mutate(ranked[int(random() * random() * len(ranked))][1]) for _ in
                          range(args.population - 1)]
    recombination = elite_configs + recombined_configs

    return (fittest, recombination)
