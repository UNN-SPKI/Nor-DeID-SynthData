#!/usr/bin/env python3

"""
split-train-holdout.py randomly samples lines from a text file to generate a training set
and holdout set of unseen examples.
"""
import pathlib
from typing import Literal
from tap import Tap
import logging
import random

class Arguments(Tap):
    input: pathlib.Path
    """The path to the file to split."""
    training: pathlib.Path
    """The filename to write the training sample to."""
    holdout: pathlib.Path
    """The filename to write the holdout sample to."""
    seed: int = None
    """The seed to use when splitting """
    holdout_size: float = 0.1
    """The ratio of lines to include in the holdout sample."""
    verbose: bool = False
    """Whether to output debugging information"""

def main(args: Arguments):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.seed:
        random.seed(args.seed)
        logging.debug(f'Setting seed to {args.seed}')
    
    with open(args.input, 'r', encoding='utf-8') as source:
        source_lines = source.readlines()

    total_holdout_lines = int(len(source_lines) * args.holdout_size)
    logging.info(f"Setting aside k={args.holdout_size} of the {len(source_lines)} lines ({total_holdout_lines} lines) for the holdout set")
    holdout_indices = random.sample(range(len(source_lines)), k=total_holdout_lines)

    training = open(args.training, 'w', encoding='utf-8')
    holdout = open(args.holdout, 'w', encoding='utf-8')
    for i, l in enumerate(source_lines):
        if i in holdout_indices:
            holdout.write(l)
        else:
            training.write(l)
    training.close()
    holdout.close()
    logging.info(f"Wrote training set to {args.training}")
    logging.info(f"Wrote holdout set to {args.holdout}")

if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
