"""
generate.py


"""
import os
import logging

from dataclasses import dataclass

from tap import Tap
import openai

OPENAI_PLACEHOLDER = 'OPENAI-KEY-HERE'


class Arguments(Tap):
    openAIKey: str = OPENAI_PLACEHOLDER
    dryRun: bool = True
    n: int = 10
    model: str = 'gpt-3.5-turbo'


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


def create_scenario() -> Scenario:
    return Scenario(givenName="Ola", familyName="Nordmann", age=45, phoneNumber="12345678",
                    city="Oslo", healthCareUnit="OUS", diagnosis="diabetes", 
                    birthDate="September 8th 1967", admissionDate="June 23rd 2023", 
                    socialSecurityNumber="15076500565")


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


def main(args: Arguments):
    if args.openAIKey == OPENAI_PLACEHOLDER and os.getenv('OPENAI_API_KEY') is None:
        logging.warning(
            "Could not find OpenAI API key, running in dry-run mode.")
        args.dryRun = True

    if args.dryRun:
        logging.warning(
            "In dry-run mode, will not send any queries to OpenAI.")
    
    scenarios = [create_scenario() for _ in range(args.n)]
    formatted_scenarios = [format_scenario(scenario) for scenario in scenarios]
    for s in formatted_scenarios:
        print(s)

if __name__ == '__main__':
    args = Arguments()
    args.parse_args()
    main(args)
