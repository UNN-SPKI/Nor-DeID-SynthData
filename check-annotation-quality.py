#!/usr/bin/env python3

import time
import os
import logging
import json
from typing import List
import re

from tap import Tap
import spacy
import spacy.training
import spacy.scorer
from spacy import displacy

from models.utilities.tags import remove_tags, list_annotations

logging.basicConfig(level=logging.DEBUG)

class ExperimentArguments(Tap):
    annotations: str = 'example.json' # The identifier of the dataset to use (see load_dataset in eval.py)
    spacyPipeline: str = 'nb_core_news_sm' # The SpaCy Language to use for tokenization
    phiOnly: bool = False # Ignore classes, force all labels into a single class
    cleanAges: bool = False # Strip "år gammel" from Age spans
    visualize: bool = False # Generate span diagrams

def visualize_example(path, example):
    comparison = {
        "text": example.reference.text,
        "spans": [{"start_token": e.start, "end_token": e.end, "label": "TRUE_" + e.label_} for e in example.reference.ents] +
                [{"start_token": e.start, "end_token": e.end, "label": "GPT_" + e.label_} for e in example.predicted.ents],
        "tokens": [str(t) for t in example.reference]
    }
    with open(path, 'w', encoding='utf-8') as example_html:
        example_html.write(displacy.render(comparison, 'span', manual=True))

def create_examples(args, nlp, example_path) -> List[spacy.training.Example]:
    examples = []
    with open(example_path, encoding='utf-8') as reference_file:
        reference_json = json.load(reference_file)
    
    for task in reference_json:
        task_text = task['text']

        reference_doc = nlp.make_doc(task_text)
        reference_ents = [reference_doc.char_span(s['start'], s['end'], label='PHI' if args.phiOnly else s['labels'][0], alignment_mode='expand') for s in task['label']]
        if args.cleanAges:
            for ent in reference_ents:
                if ent.text.endswith('år'):
                    ent.end -= 1
                elif ent.text.endswith('år gammel'):
                    ent.end -= 2
        else:
            pass
        reference_doc.set_ents(reference_ents)
        
        predicted_doc = nlp.make_doc(task_text) # Make a new document but with the same tokenization
        predicted = task['original_text']
        predicted_entities = list_annotations(predicted)
        predicted_spans = [predicted_doc.char_span(s[0], s[1], label='PHI' if args.phiOnly else s[2], alignment_mode='expand') for s in predicted_entities]
        if args.cleanAges:
            for ent in predicted_spans:
                if ent.text.endswith('år'):
                    ent.end -= 1
                elif ent.text.endswith('år gammel'):
                    ent.end -= 2
        else:
            pass
        predicted_doc.set_ents(predicted_spans)

        example = spacy.training.Example(predicted_doc, reference_doc)
        if args.visualize:
            visualize_example(f"tmp/viz/{task['id']}.html", example)

        examples.append(example)
    return examples

def main(args: ExperimentArguments):
    logging.debug(f'Loading pipeline {args.spacyPipeline}')
    nlp = spacy.load(args.spacyPipeline, enable=['ner'])

    answers = create_examples(args, nlp, example_path=args.annotations)
    scorer = spacy.scorer.Scorer(nlp)
    evaluation = scorer.score(answers)
    print(evaluation)

if __name__ == '__main__':
    args = ExperimentArguments().parse_args()
    main(args)