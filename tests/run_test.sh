#! /bin/bash
export PYTHONPATH="$PYTHONPATH:../"
source ../env/bin/activate
pip install pytest
pytest
