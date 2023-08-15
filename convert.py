#!/usr/bin/env python3
import pathlib
import json
from typing import Literal
from tap import Tap

import utilities.tags

class Arguments(Tap):
    input: pathlib.Path = 'results.json'
    """The JSON file with annotated notes to convert to a specific format."""
    output: pathlib.Path = 'results.csv'
    """The filename or directory to write converted documents to."""
    format: Literal['csv', 'xml', 'labelstudio'] = 'csv'
    """The format to convert notes to."""

def main(args: Arguments):
    with open(args.input, 'r', encoding='utf8') as input_file:
        source = json.load(input_file)
    
    if args.format == 'csv':
        create_csv(source, args.output, args)
    elif args.format == 'xml':
        create_xml(source, args.output, args)
    elif args.format == 'labelstudio':
        create_labelstudio(source, args.output, args)
    else:
        raise ValueError(f"Unrecognized format '{args.format}'")

def create_csv(source, output_path: pathlib.Path, args: Arguments):
    with open(output_path, 'w', encoding='utf8') as output:
        output.write('source_text,target_text\n')
        results = source['results']
        for r in results:
            source_text = utilities.tags.remove_tags(r).replace('\n', ' ')
            target_text = utilities.tags.redact_tags(r).replace('\n', ' ')
            output.write(f'"{source_text}","{target_text}"\n')

def create_xml(source, output_path: pathlib.Path, args: Arguments):
    with open(output_path, 'w', encoding='utf8') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>')
        results = source['results']
        for i, r in enumerate(results):
            output.write(f"<record id='{i}'>")
            output.write(r)
            output.write(f"</record>")

def create_labelstudio(source, output_path: pathlib.Path, args: Arguments):
    results = source['results']
    tasks = [{'id': i, 'data': {'text': utilities.tags.remove_tags(r), 'original_text': r}, } for i, r in enumerate(results)]
    with open(output_path, 'w', encoding='utf8') as output:
        json.dump(tasks, output)

if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)