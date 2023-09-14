pipenv run python ./convert.py --input ./dataset/training.json --output ./dataset/spacy/training.spacy --format spacy
pipenv run python ./convert.py --input ./dataset/validation.json --output ./dataset/spacy/validation.spacy --format spacy
pipenv run python ./convert.py --input ./dataset/holdout.json --output ./dataset/spacy/holdout.spacy --format spacy