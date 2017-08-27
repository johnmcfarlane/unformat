#!/usr/bin/env python3

from argparse import ArgumentParser
from glob import glob
from multiprocessing import cpu_count, Pool
from sys import stderr, stdout

from config import ClangFormatBackend, UncrustifyBackend, make_initial_configs, present_config
from measure import measure
from recombine import recombine


# If the best result yet was found last time, increase mutation a lot.
# Rationale: a new seam of fitness has been found so spread out to scan the area.
mutation_factor_progress   = 1.50

# If a joint-best result was found last time, nudge mutation down.
# Rationale: we're onto a good thing; concentrate the search.
mutation_factor_stagnation = 0.95

# If every result scored the same as the best, increase mutation a great deal.
# Rationale: no progress has been made and search is narrow; assume a minimum.
mutation_factor_stasis     = 100.00

# If only worse results were found last time, drop mutation down.
# Rationale: the guidance provided by the elite is too weak.
mutation_factor_regress    = 0.75


def gather_source_filenames(examples):
    globs = [glob(example) for example in examples]
    source_filenames = [source_filename for glob in globs for source_filename in glob]

    if not source_filenames:
        paths = str.join(" or ", ['"{}"'.format(example) for example in args.examples])
        exit("Failed to find example source files in {}.".format(paths))

    return source_filenames


class MeasureConfigTask:
    def __init__(self, source_filenames, args):
        self._source_filenames = source_filenames
        self._args = args

    def __call__(self, config):
        return (measure(config, self._source_filenames, self._args), config)


def evaluate_population(population, source_filenames, args, pool):
    task = MeasureConfigTask(source_filenames, args)
    return pool.map(task, population)


def generate(elite, population, source_filenames, mutation, args, pool):
    evaluated_population = evaluate_population(population, source_filenames, args, pool)

    scored_population = [(score, config) for score, config in evaluated_population if score]
    if not scored_population:
        exit("Failed to score any config files. (Does the given config file run on the given source files?)")

    return recombine(elite, scored_population, mutation, args)


def main(args, pool):
    elite = None
    generations_since_progress = 0
    mutation = args.mutation

    def make_elite(best):
        present_config(best[1], args, exiting=False)
        return best

    def signature(config):
        return config[0]

    try:
        source_filenames = gather_source_filenames(args.examples)
        population = make_initial_configs(args)

        stdout.flush()

        for generation in range(1000000):
            print("g={:<3}: ".format(generation), file=stderr, flush=True, end='')
            if elite:
                print("{} ".format(signature(elite)), file=stderr, flush=True, end='')
            print("m={:<5e} ".format(mutation), file=stderr, flush=True, end='')

            if generations_since_progress > args.generations:
                print("\nNo progress in {} generations; giving up.".format(generations_since_progress), file=stderr)
                break

            (generation_best, generation_worst, population) = generate(elite, population, source_filenames, mutation, args, pool)
            print(" ({}..{})".format(signature(generation_best), signature(generation_worst)), file=stderr, flush=True)

            # Choose the elite configuration.
            if not elite:
                # First time around, there is no elite yet.
                elite = make_elite(generation_best)
            elif generation_best[0] > elite[0]:
                # Regression: this generations's best score is worse than the best ever.
                mutation *= mutation_factor_regress
                generations_since_progress += 1
            else:
                if generation_best[0] < elite[0]:
                    # Progression: this generation's best score is better than the best ever.
                    mutation *= mutation_factor_progress
                    generations_since_progress = 0
                else:
                    # No progress: this generation's best score is equal to the best ever.
                    generations_since_progress += 1

                    if generation_worst[0] == elite[0]:
                        # Stasis: this entire generation is equal to the best ever.
                        mutation *= mutation_factor_stasis
                    else:
                        # Stagnation: this generation's best score is equal to the best ever.
                        mutation *= mutation_factor_stagnation

                # Promote drift by varying elite choice as much as possible.
                elite = make_elite(generation_best)

                if all([score == 0 for score in elite[0]]):
                    # The perfect score.
                    print("Matching configuration file found.", file=stderr)
                    break

            assert(mutation > 0)
            mutation = min(1., mutation)

    except KeyboardInterrupt:
        print("\nProgram interrupted.", file=stderr)
    finally:
        if elite:
            present_config(elite[1], args, exiting=True)


if __name__ == "__main__":
    parser = ArgumentParser(description="generates configuration file for code formatting untility from example codebase")

    parser.add_argument("-c", "--command", help="clang-format / uncrustify command")
    parser.add_argument("-d", "--debug", help="print oodles of debugging output")
    parser.add_argument("-f", "--cf", help="use clang-format", dest="backend", action="store_const", const=ClangFormatBackend)
    parser.add_argument("-g", "--generations", help="maximum number of generations without progress", type=int, default=50)
    parser.add_argument("-i", "--initial", help="initial configuration file (\"\" for tool defaults)", default=None)
    parser.add_argument("-j", "--jobs", help="number of parallel processes", type=int, default=cpu_count())
    parser.add_argument("-m", "--mutation", help="initial mutation rate", type=float, default=0.05)
    parser.add_argument("-p", "--population", help="population size", type=int, default=40)
    parser.add_argument("-r", "--root", help="project root (location for configuration file)")
    parser.add_argument("-u", "--uncrustify", help="use uncrustify (default)", dest="backend", action="store_const", const=UncrustifyBackend)
    parser.add_argument("examples", help="path to example source files", nargs='+')

    args = parser.parse_args()

    args.backend = args.backend or ClangFormatBackend
    args.command = args.command or args.backend.default_command()
    # args.mutation_rules = args.backend.mutation_rules(args, mutate)

    with Pool(args.jobs) as pool:
        main(args, pool)
