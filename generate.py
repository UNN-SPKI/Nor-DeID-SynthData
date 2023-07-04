"""
generate.py


"""
import os
import logging
import pathlib
import random
import datetime

from dataclasses import dataclass
from typing import List

from tap import Tap
import openai

OPENAI_PLACEHOLDER = 'OPENAI-KEY-HERE'


class Arguments(Tap):
    openAIKey: str = OPENAI_PLACEHOLDER
    dryRun: bool = True
    n: int = 10
    model: str = 'gpt-3.5-turbo'
    locale: str = 'nb'
    seed: int = 42


@dataclass
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
    random.seed(args.seed)
    if args.openAIKey == OPENAI_PLACEHOLDER and os.getenv('OPENAI_API_KEY') is None:
        logging.warning(
            "Could not find OpenAI API key, running in dry-run mode.")
        args.dryRun = True

    if args.dryRun:
        logging.warning(
            "In dry-run mode, will not send any queries to OpenAI.")

    scenarios = create_scenarios(args.n, args.locale)
    formatted_scenarios = [format_scenario(scenario) for scenario in scenarios]
    for s in formatted_scenarios:
        print(s)


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

    # Not strictly correct, doesn't take leap years into account
    ages = [(b - today).days // 365 for b in birth_dates]

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


if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
