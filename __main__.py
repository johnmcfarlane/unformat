#!/usr/bin/env python3

from argparse import ArgumentParser
from glob import glob
from multiprocessing import cpu_count, Pool
from sys import stderr

from config import make_initial_configs, present_config
from measure import MeasureConfigTask
from recombine import recombine


def gather_source_filenames(examples):
    globs = [glob(example) for example in examples]
    source_filenames = [source_filename for glob in globs for source_filename in glob]

    if not source_filenames:
        paths = str.join(" or ", ['"{}"'.format(example) for example in args.examples])
        exit("Failed to find example source files in {}.".format(paths))

    return source_filenames


def score_population(population, source_filenames, args, pool):
    task = MeasureConfigTask(source_filenames, args)
    return pool.map(task, population)


def generate(population, source_filenames, args, pool):
    scored_population = score_population(population, source_filenames, args, pool)
    return recombine(scored_population, args)


def main(args, pool):
    fittest = None

    try:
        source_filenames = gather_source_filenames(args.examples)
        population = make_initial_configs(args)

        for generation in range(args.generations):
            print("{}: ".format(generation), end='', file=stderr, flush=True)
            (generation_fittest, population) = generate(population, source_filenames, args, pool)
            print(" {}".format(generation_fittest[0]), file=stderr, flush=True)

            if not fittest or generation_fittest[0] < fittest[0]:
                fittest = generation_fittest
                present_config(fittest[1], args, exiting=False)

                if all([score == 0 for score in fittest[0]]):
                    print("Matching configuration file found.", file=stderr)
                    break

    except KeyboardInterrupt:
        print("\nProgram interrupted.", file=stderr)
    finally:
        if fittest:
            present_config(fittest[1], args, exiting=True)


if __name__ == "__main__":
    parser = ArgumentParser(description="generates .clang-format file from example codebase")

    parser.add_argument("-c", "--command", help="clang-format command", default="clang-format")
    parser.add_argument("-g", "--generations", help="maximum number of generations", type=int, default=1000000)
    parser.add_argument("-i", "--initial", help="initial .clang-format file (\"\" for clang-format default styles)", default=None)
    parser.add_argument("-j", "--jobs", help="number of parallel processes", type=int, default=cpu_count())
    parser.add_argument("-m", "--mutation", help="mutation rate", type=float, default=0.05)
    parser.add_argument("-p", "--population", help="population size", type=int, default=40)
    parser.add_argument("-r", "--root", help="project root (location for .clang-format file)")
    parser.add_argument("-l", "--lock", metavar="ClangFormatKey", action="append", help="prevent mutation of the given key")
    parser.add_argument("examples", help="path to example source files", nargs='+')

    args = parser.parse_args()

    with Pool(args.jobs) as pool:
        main(args, pool)
