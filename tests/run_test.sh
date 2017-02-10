#! /bin/bash
export PYTHONPATH="$PYTHONPATH:../"
source ../env/bin/activate
pytest
