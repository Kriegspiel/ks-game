# Python Kriegspiel Game

[![Build Status](https://travis-ci.org/Kriegspiel/ks-game.svg?branch=master)](https://travis-ci.org/Kriegspiel/ks-game)
[![PyPI version](https://badge.fury.io/py/kriegspiel.svg)](https://badge.fury.io/py/kriegspiel)
[![codecov](https://codecov.io/gh/Kriegspiel/ks-game/branch/master/graph/badge.svg)](https://codecov.io/gh/Kriegspiel/ks-game)

---

## Kriegspiel Game Engine

Supported Kriegspiel rules:

1. Berkeley
2. Berkeley + Any

In plan:

1. Crazykrieg
2. Crazykrieg + Any


## How-to

### Install

```bash
pip install kriegspiel
```

### Run tests

```bash
# clone this repo
git clone git@github.com:Kriegspiel/ks-game.git
# activate virtual env (optional)
cd ks-game
python3 -m venv ks-game-env
source ks-game-env/bin/activate
# install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
# run tests
python -m pytest tests/
```

### Lint

```bash
black -l 128 %FILE%
```
