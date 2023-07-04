"""
generate.py


"""
import json
import os
import logging
import pathlib
import random
import datetime

import dataclasses
from typing import List, Literal

from tap import Tap
import openai

OPENAI_PLACEHOLDER = 'OPENAI-KEY-HERE'


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
    givenName: str
    familyName: str
    age: int
    phoneNumber: str
    city: str
    healthCareUnit: str
    diagnosis: str
    birthDate: str
    admissionDate: str
    socialSecurityNumber: str


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
    scenarios = create_scenarios(args.n, args.locale)

    logging.info("Formatting test cases as prompts.")
    prompts = [format_scenario(scenario) for scenario in scenarios]

    logging.info("Sending prompts to completion.")
    completed_notes = [complete_note(prompt, args)
                       for prompt in prompts]
    
    logging.info(f"Writing results to {args.output}")
    
    with open(args.output, 'w', encoding='utf8') as result_file:
        args.openAIKey = OPENAI_PLACEHOLDER
        results = {'parameters': args.as_dict(), 'scenarios': [dataclasses.asdict(s) for s in scenarios], 'prompts': prompts, 'results': completed_notes}
        json.dump(results, result_file, ensure_ascii=False)


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


def generate_random_date(start_date: datetime.date, end_date: datetime.date) -> str:
    random_days = random.randint(0, (end_date - start_date).days)
    random_date = start_date + datetime.timedelta(days=random_days)

    return random_date


def generate_random_phone(locale: str) -> str:
    phone = str(random.randint(0, 1e8-1)).zfill(8)
    return random.choice([phone, f'0047{phone}', f'+47{phone}'])


def generate_random_ssn(locale: str) -> str:
    ssn = str(random.randint(0, 1e11-1)).zfill(11)
    return random.choice([ssn, f'{ssn[0:6]} {ssn[6:]}'])


def create_scenarios(n: int, locale: str) -> List[Scenario]:
    given_names = sample_lines('vocabularies/nb_given_names.csv', n)
    family_names = sample_lines('vocabularies/nb_family_names.csv', n)
    diagnoses = sample_lines('vocabularies/en_diagnoses.csv', n)
    healthcare_units = sample_with_replacement(
        'vocabularies/nb_healthcare_units.csv', n)

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

    return [Scenario(givenName=given_names[i],
                     familyName=family_names[i],
                     age=ages[i],
                     phoneNumber=phone_numbers[i],
                     city="Oslo",
                     healthCareUnit=healthcare_units[i],
                     diagnosis=diagnoses[i],
                     birthDate=written_birth_dates[i],
                     admissionDate=written_admissions[i],
                     socialSecurityNumber=ssns[i])
            for i in range(n)]


def format_scenario(scenario: Scenario) -> str:
    return f"""
Write a discharge summary in Norwegian for a patient named {scenario.givenName} {scenario.familyName}, who has been diagnosed with {scenario.diagnosis}.
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

Epikrise:
"""


def complete_note(prompt: str, args: Arguments) -> str:
    if args.dryRun:
        logging.debug("Not forwarding to OpenAI.")
        return ""

    if os.getenv('OPENAI_API_KEY') is None:
        openai.api_key = args.openAIKey

    completion = openai.ChatCompletion.create(
        model=args.model,
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.topP)
    answer = completion.choices[0].message.content
    return answer


if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
