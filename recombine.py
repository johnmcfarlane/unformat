from random import random, choice
from sys import stderr


def mutate_value(key, value, mutate_args):
    mutation_rules = mutate_args["mutation_rules"]
    if key in mutation_rules:
        mutation_rule = mutation_rules[key]
        mutated_value = mutation_rule(value, mutate_args)
        return mutated_value

    if isinstance(value, bool):
        return not value

    print("Unrecognized setting, '{}: {}', in .clang-format configuration.".format(key, value), file=stderr)
    return value


def visit_line(key, value, mutate_args):
    return mutate_value(key, value, mutate_args) if random() < mutate_args["probability"] else value


def crossover_value(parent1, parent2, key):
    assert(key in parent1 or key in parent2)

    if key not in parent1:
        return parent2[key]

    if key not in parent2:
        return parent1[key]

    value1 = parent1[key]
    value2 = parent2[key]
    assert(type(value1) == type(value2))

    if type(value1) is dict:
        return crossover(value1, value2)
    else:
        return choice([value1, value2])


def crossover(parent1, parent2):
    parent1_keys = parent1.keys()
    parent2_keys = parent2.keys()
    keys = set(parent1_keys).union(parent2_keys)
    assert(len(keys) == len(parent1_keys) == len(parent2_keys))

    return {key: crossover_value(parent1, parent2, key) for key in keys}


def mutate(config, mutate_args):
    return {key: visit_line(key, value, mutate_args) for key, value in config.items()}


def choose_from_ranked(ranked):
    i = int(random() * random() * len(ranked))
    return ranked[i]


# returns tuple of:
# - best (fittest) individual from population and
# - worst (least fit) individual from population and
# - next generation of mutated offspring selected from elite and population
def recombine(elite, population, mutation, args):
    sort_key = lambda scored: scored[0]

    unranked = population
    if elite:
        unranked.append(elite)
    ranked = sorted(unranked, key=sort_key)

    mutate_args = {
        "probability": mutation,
        "mutation_rules": args.backend.mutation_rules(args, mutate)
    }
    def make_offspring():
        parent1 = choose_from_ranked(ranked)
        parent2 = choose_from_ranked(ranked)
        crossed = crossover(parent1[1], parent2[1])
        mutation = mutate(crossed, mutate_args)
        args.backend.sanitize(mutation)
        return mutation

    recombined_configs = [make_offspring() for _ in range(args.population)]

    best = min(population, key=sort_key)
    worst = max(population, key=sort_key)

    # cannot pass args to MP pool with mutation_rules in it
    return (best, worst, recombined_configs)
