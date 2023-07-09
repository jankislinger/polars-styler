# Example Notebooks

## Setup

```shell
poetry shell
poetry install
pip install ../..
jupyter lab
```

## Before commit

```shell
jupyter nbconvert \
  --ClearMetadataPreprocessor.enabled=True \
  --ClearOutputPreprocessor.enabled=True \
  --to=notebook \
  --inplace \
  Example1.ipynb
```