black oarepo_doi tests --target-version py310
autoflake --in-place --remove-all-unused-imports --recursive oarepo_doi tests
isort oarepo_doi tests  --profile black
