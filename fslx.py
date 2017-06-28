#!/bin/env python
"""
FSLX.py is an attempt of extending FSLX and controlling it's complexity.
It's goal is to be safer to use, provide better error handling, and
offer support for arbitrary output directories.
"""
import os
import argparse
import random
import textwrap
import subprocess
from collections import namedtuple
from functools import wraps

# A NamedTuple to store the relevant information for each operation.
Operations = namedtuple('FSLX_Operation',
                        'name, command, argument, pipe, parallel')
Operations.__new__.__defaults__ = (None, None, None, False, False)

# A Dictionary containing all implemented FSLX operations.
IMPLEMENTED_OPERATIONS = {}


def operate(name, argument=None, pipe=False, parallel=False):
    """OPERATE automatically registers a FSLX operation into the
    IMPLEMENTED_OPERATIONS dictionary.

    :param name: The name of the operation
    :param pipe: Whether the operation allows further pipeing.
    :param parallel: Whether the operation is ridiculously parallel.
    :returns: The decorated function
    :rtype: Function

    """
    def real_operate(func):
        IMPLEMENTED_OPERATIONS[name] = Operations(name, func,
                                                  argument=argument,
                                                  pipe=pipe,
                                                  parallel=parallel)

        @wraps(func)
        def op(*args, **kwargs):
            return func(*args, **kwargs)

        return op

    return real_operate


@operate('nvols')
def nvols(inputfile):
    """
    Return the number of volumes in a 4D NIfTI file.
    If the input is 3D, return 1.
    """
    fsl_command = 'fslnvols'
    command = [fsl_command, inputfile]
    print(subprocess.check_output(command).decode('utf-8'))


def check_inputs(inputfiles):
    """Check if all inputs are valid for FSLX.

    :param inputfiles: An iterable with filenames
    :returns: None
    :rtype: None

    """
    for inputfile in inputfiles:
        if not os.path.exists(inputfile):
            print(f"FSLX cannot find $inputfile")
            raise FileExistsError


if __name__ == "__main__":

    quotes = ["No one can be told what the Matrix is. You must see if for yourself.",
              "Welcome to the desert of the real.",
              "Free your mind.",
              """
              Throughout human history, we have been dependent on machines to survive.
              Fate, it seems, is not without a sense of irony.
              """,
              "Welcome to the real world.",
              "Never send a human to do a machine job."]


    description = """
FSLX is a *dumb* wrapper around some of fsltools. It exists so we don't have
to remember the arbitrary names of FSL tools,nor the inconsistent parameter
naming conventions of each of them. FSLX also accepts multiple images as input
to perform the same operations in parallel.

Optional arguments '--target-directory' and '--in-place' must come *before*
the operation and its inputs.

Example: fslx.py --in-place --target-directory "$HOME" moco img1 img2
                  """

    # Parent parser with common stuff.
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument('-t', '--target-directory', type=str, default='.',
                        help="An output directory to store output files.")
    parent.add_argument('-i', '--in-place', action='store_true',
                        help="After succesful execution, delete the inputs.")
    parent.add_argument('inputfiles', nargs='*', type=argparse.FileType('r'),
                        help="A list of input types to operate on.")

    # Top level parser.
    parser = argparse.ArgumentParser(prog="FSLX",
                                     epilog=textwrap.dedent(random.choice(quotes)),
                                     description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parent])

    # Operation parsers.
    subparsers = parser.add_subparsers(help='Sub-command help', dest='chosen_op')

    op_parsers = {}
    for op_name, op in IMPLEMENTED_OPERATIONS.items():
        op_parsers[op_name] = subparsers.add_parser(op_name,
                                                    description=op.command.__doc__,
                                                    parents=[parent])
        if op.argument is not None:
            op_parsers[op_name].add_argument(op.argument)
        # op_parsers[op_name].add_argument('inputfiles', nargs='*', type=argparse.FileType('r'),
        #                                  help="A list of input types to operate on.")




    args = parser.parse_args()
    op_args = {}
    for key, subparser in op_parsers.items():
        op_args[key] = subparser.parse_args()

    print(args.chosen_op)
