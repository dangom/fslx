#!/usr/bin/env python3
"""
FSLX.py is an attempt of extending FSLX and controlling it's complexity.
It's goal is to be safer to use, provide better error handling, and
offer support for arbitrary output directories.
"""
import argparse
import os
import random
import subprocess
import tempfile
import textwrap
from collections import namedtuple
from functools import wraps

import nibabel as nib  # Only to read the TR.

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

def fslx_output_handler(inputfile, suffix, targetdir=None):
    """Add a suffix to the inputfile, and change its
    directory. The result can be used as a filename for
    outputfiles. If targetdir is None, then do not change it.

    :param inputfile: A filename
    :param suffix: A suffix to append to the filename
    :param targetdir: Change the input filename to target dir.
    :returns: outputfile
    :rtype: String

    """
    pass


@operate('nvols')
def nvols(inputfile):
    """
    Return the number of volumes in a 4D NIfTI file.
    If the input is 3D, return 1.
    """
    fsl_command = 'fslnvols'
    command = [fsl_command, inputfile]
    print(subprocess.check_output(command).decode('utf-8'))


@operate('highpass', 'sigma', True, True)
def highpass(inputfile, sigma, targetdir=None):

    tr = nib.load(inputfile).header.structarr['pixdim'][4]
    cutoff_s = 1/tr * sigma/2
    fsl_command = 'fslmaths'
    # Step 1, compute the mean.
    temp = tempfile.mkstemp('_FSLX.nii.gz', 'hpass_mean_')
    command = [fsl_command, inputfile, '-Tmean', temp[1]]
    res = subprocess.check_output(command)

    # Step 2, highpass and add the mean back.

    outputfile = fslx_output_handler(inputfile, suffix, targetdir)

    cutoff_arg = '-btpf -1'
    command = [fsl_command, inputfile, cutoff_arg, str(sigma),
               '-add', temp[1], outputfile]
    res = subprocess.check_output(command)


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
    # parent.add_argument('inputfiles', nargs='*', type=argparse.FileType('r'),
    #                     help="A list of input files to operate on.")

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
        op_parsers[op_name].add_argument('inputfiles', nargs='*', type=argparse.FileType('r'),
                                         help="A list of input types to operate on.")


    # parser.add_argument('inputfiles', nargs='*', type=argparse.FileType('r'),
    #                     help="A list of input files to operate on.")


    args = parser.parse_args()

    for inputfile in args.inputfiles:
        IMPLEMENTED_OPERATIONS[args.chosen_op].command(inputfile.name)
