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
    format: Literal['csv', 'xml', 'labelstudio', 'spacy', 'text'] = 'csv'
    """The format to convert notes to."""
    section: Literal['cleaned', 'results'] = 'cleaned'
    """Whether to use the cleaned texts under 'cleaned_results' or the original annotated examples under 'results' """

def main(args: Arguments):
    with open(args.input, 'r', encoding='utf8') as input_file:
        source = json.load(input_file)

    section_name = "cleaned_results" if args.section == 'cleaned' else "results"
    
    if args.format == 'csv':
        create_csv(source, section_name, args.output, args)
    elif args.format == 'xml':
        create_xml(source, section_name, args.output, args)
    elif args.format == 'labelstudio':
        create_labelstudio(source, section_name, args.output, args)
    elif args.format == 'spacy':
        create_spacy(source, section_name, args.output, args)
    elif args.format == 'text':
        create_text(source, section_name, args.output, args)
    else:
        raise ValueError(f"Unrecognized format '{args.format}'")

def create_csv(source, section_name, output_path: pathlib.Path, args: Arguments):
    with open(output_path, 'w', encoding='utf8') as output:
        output.write('source_text,target_text\n')
        results = source[section_name]
        for r in results:
            source_text = utilities.tags.remove_tags(r).replace('\n', ' ')
            target_text = utilities.tags.redact_tags(r).replace('\n', ' ')
            output.write(f'"{source_text}","{target_text}"\n')

def create_xml(source, section_name, output_path: pathlib.Path, args: Arguments):
    with open(output_path, 'w', encoding='utf8') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>')
        results = source[section_name]
        for i, r in enumerate(results):
            output.write(f"<record id='{i}'>")
            output.write(r)
            output.write(f"</record>")

def create_labelstudio(source, section_name, output_path: pathlib.Path, args: Arguments):
    results = source[section_name]
    tasks = [{'id': i, 'data': {'text': utilities.tags.remove_tags(r), 'original_text': r}, } for i, r in enumerate(results)]
    with open(output_path, 'w', encoding='utf8') as output:
        json.dump(tasks, output)

def create_spacy(source, section_name, output_path: pathlib.Path, args: Arguments):
    results = source[section_name]
    EXPECTED_TAGS = ['First_Name', 'Last_Name', 'Location', 'Health_Care_Unit', 'Age', 'Phone_Number', 'Social_Security_Number', 'Date', 'PHI']

    import spacy
    doc_bin = spacy.tokens.DocBin()
    nlp = spacy.load('nb_core_news_sm')
    for r in results:
        doc_text = utilities.tags.remove_tags(r).replace('\n', ' ')
        annotations = utilities.tags.list_annotations(r, EXPECTED_TAGS)
        doc = nlp.make_doc(doc_text)
        ents = [
            doc.char_span(a[0], a[1], a[2], alignment_mode='expand') for a in annotations
        ]
        doc.set_ents(ents)
        doc_bin.add(doc)
    doc_bin.to_disk(output_path)

def create_text(source, section_name, output_path: pathlib.Path, args: Arguments):
    results = source[section_name]
    for i, r in enumerate(results):
        target_path = output_path / f"{i}.txt"
        with open(target_path, 'w', encoding='utf8') as target:
            target.write(utilities.tags.remove_tags(r).replace('\n', ' '))


if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)