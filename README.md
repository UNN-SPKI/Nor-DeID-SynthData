# Nor-DeID-SynthData

Synthetic discharge summaries in Norwegian for comparing deidentification methods for the article [Instruction-guided deidentification with synthetic test cases for Norwegian clinical text](https://proceedings.mlr.press/v233/lund24a.html).

## Dataset

The dataset is available in JSON format and as a SpaCy DocBin under [Releases](https://github.com/UNN-SPKI/Nor-DeID-SynthData/releases).

## Citing

Cite the dataset as

```
@InProceedings{pmlr-v233-lund24a,
  title = 	 {Instruction-guided deidentification with synthetic test cases for Norwegian clinical text},
  author =       {Lund, J{\o}rgen Aarmo and Mikalsen, Karl {\O}yvind and Burman, Joel and Woldaregay, Ashenafi Zebene and Jenssen, Robert},
  booktitle = 	 {Proceedings of the 5th Northern Lights Deep Learning Conference ({NLDL})},
  pages = 	 {145--152},
  year = 	 {2024},
  editor = 	 {Lutchyn, Tetiana and Ramírez Rivera, Adín and Ricaud, Benjamin},
  volume = 	 {233},
  series = 	 {Proceedings of Machine Learning Research},
  month = 	 {09--11 Jan},
  publisher =    {PMLR},
  pdf = 	 {https://proceedings.mlr.press/v233/lund24a/lund24a.pdf},
  url = 	 {https://proceedings.mlr.press/v233/lund24a.html}
}
```

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

To create a CSV dataset, call `convert.py` with `--format` set to the format you want, and `--output` pointing to the file or directory the converted documents should be stored in:

`(venv) $ python convert.py --input results.json --output results.csv --format csv`
