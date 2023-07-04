# Nor-DeID-SynthData

Synthetic discharge summaries in English and Norwegian for comparing deidentification methods 

## Setup

You can set up the utility through Pipenv:

```
$ pip install --upgrade pipenv
$ pipenv sync
```

Alternatively, you can set up the utility with a regular virtual environment:

```
$ python -m venv venv
$ venv/Scripts/activate
(venv) $ pip install -r requirements.txt
```

## Using

Invoke `generate.py` with `--n` to the number of records you would like to generate, `--output` to the file the results should be put in, and `--openAIKey` set to your OpenAI API key:

`(venv) $ python generate.py --n 100 --output results.json --openAIKey sk-...`

You can get a list of arguments with `-h`:

`(venv) $ python generate.py -h`

