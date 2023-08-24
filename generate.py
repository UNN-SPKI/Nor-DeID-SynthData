#!/usr/bin/env python3
"""
generate.py

Call OpenAI's chat completion to generate synthetic discharge summaries in English and Norwegian with annotated PHI
"""
import csv
import json
import os
import logging
import pathlib
import random
import datetime

import dataclasses
from typing import List, Literal, Tuple

from tap import Tap
import openai

OPENAI_PLACEHOLDER = 'OPENAI-KEY-HERE'
SYSTEM_PROMPT = """
Answer in the form of an annotated discharge note from a specialist. Include details about each finding.
"""

class Arguments(Tap):
    openAIKey: str = OPENAI_PLACEHOLDER
    """The API key to OpenAI"""
    dryRun: bool = False
    """If set, does not issue any requests to OpenAI"""
    n: int = 10
    """The number of records to generate"""
    model: str = 'gpt-3.5-turbo'
    """Which OpenAI model to prompt"""
    locale: Literal['nb', 'en'] = 'nb'
    """Which language to fetch vocabularies from and generate summaries in"""
    split: Literal['all', 'training', 'holdout'] = 'all'
    """Which split of texts to draw samples from (see split-train-holdout.py)"""
    seed: int = 42
    """The seed for the random generator (note: must set --n the same to get same prompts)"""
    verbose: bool = False
    """Whether to output debugging information"""
    output: str = 'results.json'
    """Which file to output results to"""
    temperature: float = 1.0
    """The model temperature (set to 0.0 to get mostly deterministic responses)"""
    topP: float = 1.0
    """Top-p for model sampling"""
    max_tokens: int = 1024
    """The upper bound on tokens to output for each document"""

@dataclasses.dataclass
class Scenario:
    """Scenario contains the parameters used to prompt the language model for a generated note."""
    locale: str
    """The intended language of the generated note, as a two-letter code ('nb' for Norwegian, 'en' for American English)"""
    noteType: str
    """The note type (e.g. 'discharge summary')"""
    translatedNoteType: str
    """The note type translated to the intended language (e.g. 'epikrise')"""
    givenName: str
    """The given/first name of the patient."""
    familyName: str
    """The family/surname of the patient."""
    age: int
    """The age of the patient."""
    phoneNumber: str
    """The patient's phone number."""
    city: str
    """The patient's city of residence."""
    healthCareUnit: str
    """The institution where the patient has been admitted."""
    diagnosis: str
    """The diagnosis or primary symptoms the patient has been admitted with (as a partial sentence, e.g. [admitted with] 'generalized abdominal pain')"""
    birthDate: str
    """The date the patient was born."""
    admissionDate: str
    """The date the patient was admitted."""
    socialSecurityNumber: str
    """A unique identifier for the patient (the US Social Security Number for English, the fødsels/personnummer for Norwegian)"""
    findings: list[str]
    """Clinical observations to include"""


def main(args: Arguments):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug(f"Running with arguments {args}")

    random.seed(args.seed)
    if args.openAIKey == OPENAI_PLACEHOLDER and os.getenv('OPENAI_API_KEY') is None:
        logging.warning(
            "Could not find OpenAI API key, running in dry-run mode.")
        args.dryRun = True

    if args.dryRun:
        logging.warning(
            "In dry-run mode, will not send any queries to OpenAI.")
    
    
    logging.info(f"Creating {args.n} test cases.")
    scenarios = create_scenarios(args.n, args.locale, args.split)

    logging.info("Formatting test cases as prompts.")
    prompts = [format_scenario(scenario) for scenario in scenarios]

    logging.info("Sending prompts to completion.")
    completed_notes = [complete_note(prompt, args)
                       for prompt in prompts]
    
    logging.info(f"Writing results to {args.output}")
    
    with open(args.output, 'w', encoding='utf8') as result_file:
        args.openAIKey = OPENAI_PLACEHOLDER
        results = {'parameters': args.as_dict(), 'scenarios': [dataclasses.asdict(s) for s in scenarios], 'prompts': prompts, 'results': completed_notes}
        json.dump(results, result_file)


def sample_lines(filename: pathlib.Path, n: int = 1):
    with open(filename, 'r', encoding='utf8') as file:
        lines = file.readlines()

    num_lines = len(lines)
    if n > num_lines:
        raise ValueError(
            f"The file {filename} only has {num_lines} lines but we requested {n} unique choices.")

    stripped_lines = [line.strip() for line in lines]
    return random.sample(stripped_lines, n)


def sample_with_replacement(filename: pathlib.Path, n: int = 1):
    with open(filename, 'r', encoding='utf8') as file:
        lines = file.readlines()

    stripped_lines = [line.strip() for line in lines]
    return random.choices(stripped_lines, k=n)

def sample_document_types(filename: pathlib.Path, task_locale: str, title_locale: str, n: int = 1) -> List[Tuple[str, str]]:
    with open(filename, 'r', encoding='utf8') as file:
        reader = csv.DictReader(file)
        records = list(reader)
    
    random_types = random.choices(records, k=n)
    return [(r[task_locale], r[title_locale]) for r in random_types]

def generate_random_date(start_date: datetime.date, end_date: datetime.date) -> str:
    random_days = random.randint(0, (end_date - start_date).days)
    random_date = start_date + datetime.timedelta(days=random_days)

    return random_date


def generate_random_phone(locale: str) -> str:
    if locale == 'nb':
        phone = str(random.randint(0, 1e8-1)).zfill(8)
        return random.choice([phone, f'0047{phone}', f'+47{phone}'])
    elif locale == 'en':
        phone = str(random.randint(0, 1e10-1)).zfill(10)
        return random.choice([phone, f'({phone[0:3]}) {phone[3:7]}-{phone[7:]}', f'+1 ({phone[0:3]}) {phone[3:7]}-{phone[7:]}'])
    else:
        raise ValueError(f"Can't generate phone number for locale {args.locale}")


def generate_random_ssn(locale: str) -> str:
    if locale == 'nb':
        ssn = str(random.randint(0, 1e11-1)).zfill(11)
        return random.choice([ssn, f'{ssn[0:6]} {ssn[6:]}'])
    elif locale == 'en':
        # Use US SSNs
        ssn = str(random.randint(0, 1e9-1)).zfill(9)
        return random.choice([ssn, f'{ssn[0:3]}-{ssn[3:5]}-{ssn[5:]}', f'{ssn[0:3]} {ssn[3:5]} {ssn[5:]}'])
    else:
        raise ValueError(f"Can't generate SSN for locale {args.locale}")
    
def sample_findings(findings_source, n: int, locale: str) -> list[list[str]]:
    patient_findings = []
    for _ in range(n):
        finding_list = [random.choice(findings_source[v]) for v in findings_source.keys()]
        random.shuffle(finding_list)
        patient_findings.append(finding_list)
    return patient_findings

def create_scenarios(n: int, locale: str, split: str='all') -> List[Scenario]:
    document_types = sample_document_types(os.path.join('vocabularies', 'document_types.csv'), 'en', locale, n)
    given_names = sample_lines(os.path.join('vocabularies', split, 'nb_given_names.csv'), n)
    family_names = sample_lines(os.path.join('vocabularies', split, 'nb_family_names.csv'), n)
    cities = sample_lines(os.path.join('vocabularies', split, 'nb_cities.csv'), n)
    diagnoses = sample_with_replacement(os.path.join('vocabularies', split, 'en_diagnoses.csv'), n)
    healthcare_units = sample_with_replacement(
        os.path.join('vocabularies', split, 'nb_healthcare_units.csv'), n)
    with open('vocabularies/en_findings.json', 'r') as findings_file:
        findings_source = json.load(findings_file)

    start_births, end_births = datetime.date(
        1943, 1, 1), datetime.date(2010, 1, 1)
    birth_dates = [generate_random_date(
        start_births, end_births) for _ in range(n)]
    written_birth_dates = [b.strftime("%B %d. %Y") for b in birth_dates]
    today = datetime.date.today()

    # Not correct, doesn't take leap years into account
    # but should be OK for the purposes of testing deidentification
    ages = [(today - b).days // 365 for b in birth_dates]

    start_admissions, end_admissions = datetime.date(
        2012, 1, 1), datetime.date(2023, 1, 1)
    admission_dates = [generate_random_date(
        start_admissions, end_admissions) for _ in range(n)]
    written_admissions = [b.strftime("%B %d. %Y") for b in admission_dates]
    phone_numbers = [generate_random_phone(locale) for _ in range(n)]

    ssns = [generate_random_ssn(locale) for _ in range(n)]

    findings = sample_findings(findings_source, n, locale)

    return [Scenario(locale=args.locale,
                     noteType=document_types[i][0],
                     translatedNoteType=document_types[i][1],
                     givenName=given_names[i],
                     familyName=family_names[i],
                     age=ages[i],
                     phoneNumber=phone_numbers[i],
                     city=cities[i],
                     healthCareUnit=healthcare_units[i],
                     diagnosis=diagnoses[i],
                     birthDate=written_birth_dates[i],
                     admissionDate=written_admissions[i],
                     socialSecurityNumber=ssns[i],
                     findings=findings[i])
            for i in range(n)]


def format_scenario(scenario: Scenario) -> str:
    lang_name = {'en': 'English', 'nb': 'Norwegian'}
    if scenario.locale not in lang_name:
        raise ValueError(f"Unknown locale {args.locale}")
    
    language = lang_name[scenario.locale]
    formatted_findings = ', '.join(scenario.findings)
    return f"""
Write a {scenario.noteType} in {language} for a patient named {scenario.givenName} {scenario.familyName}, who has been admitted with the primary diagnosis code \"{scenario.diagnosis}\".
It should explain that at the time of admission, the patient had {formatted_findings}.
Additionally, include the following information:
- The patient is {scenario.age} years old.
- The patient was admitted to {scenario.healthCareUnit} on {scenario.admissionDate}.
- The patient was born in {scenario.city} on {scenario.birthDate}.
- The patient's phone number is {scenario.phoneNumber}.
- The patient's social security number is {scenario.socialSecurityNumber}.

For every first name in the text, add surrounding <First_Name> tags.
For every last name in the text, add surrounding <Last_Name> tags.
For every person's age in the text, add surrounding <Age> tags.
For every telephone number in the text, add surrounding <Phone_Number> tags.
For every social security number in the text, add surrounding <Social_Security_Number> tags.
For every hospital, healthcare institution and healthcare provider, add surrounding <Health_Care_Unit> tags.
For every other location in the text, add surrounding <Location> tags.
For every date in the text, add surrounding <Date> tags.
Do not add any other tags.

"""


def complete_note(prompt: str, args: Arguments) -> str:
    if args.dryRun:
        return ""

    if os.getenv('OPENAI_API_KEY') is None:
        openai.api_key = args.openAIKey

    completion = openai.ChatCompletion.create(
        model=args.model,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
            ],
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.topP)
    answer = completion.choices[0].message.content
    return answer


if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
