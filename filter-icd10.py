#!/usr/bin/env python3
"""
filter-icd10.py tries to finds a subset of ICD-10 codes that are applicable as
principal/primary diagnosis codes.
"""
import pathlib
from typing import Literal
from tap import Tap
import logging

class Arguments(Tap):
    input: pathlib.Path = 'vocabularies/icd10cm-codes-April-1-2023.txt'
    """The path to the full list of ICD-10 diagnosis codes."""
    output: pathlib.Path = 'vocabularies/en_diagnoses.csv'
    """The filename or directory to write the subset of diagnosis codes to."""
    verbose: bool = False
    """Whether to output debugging information"""

def include(code: str, name: str) -> bool:
    logging.debug(f"Checking {code=}, {name=}")
    
    # We exclude mental and behavioral disorder codes,
    # and codes which are primarily secondary:
    if code[0] in ['F', 'Z', 'Y', 'U']:
        return False
    
    name_lowered = name.lower()
    if 'personal history of' in name_lowered:
        return False
    
    if 'status' in name_lowered:
        return False
    
    if 'unspecified' in name_lowered:
        return False
    
    if 'other' in name_lowered:
        return False
    
    return True

def clean(name: str) -> str:
    return name.split(',', maxsplit=1)[0]

def main(args: Arguments):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    diagnoses = set()
    with open(args.input, 'r') as code_file:
        for line in code_file:
            split_line = line.split(' ', maxsplit=1)
            code, name = split_line[0], split_line[1].strip()
            if include(code, name):
                logging.debug(f"Cleaning {name=}")
                cleaned_name = clean(name)
                logging.debug(f"Adding {cleaned_name=}")
                diagnoses.add(code + " " + cleaned_name + '\n')
            else:
                logging.debug(f"Excluded {name=}")

    with open(args.output, 'w', encoding='utf-8') as output_file:
        output_file.writelines(list(diagnoses))

if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
