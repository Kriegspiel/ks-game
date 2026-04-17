# kriegspiel

[![PyPI version](https://badge.fury.io/py/kriegspiel.svg)](https://pypi.org/project/kriegspiel/)

Python game engine for the Berkeley Kriegspiel referee rules.

Current scope:
- Berkeley Kriegspiel
- Berkeley + Any

The package models the referee, not a UI. You interact with it by asking questions as `KriegspielMove` objects and reading `KriegspielAnswer` results.

## Install

```bash
pip install kriegspiel
```

## Quick Start

```python
import chess

from kriegspiel.berkeley import BerkeleyGame
from kriegspiel.move import KriegspielMove, QuestionAnnouncement

game = BerkeleyGame(any_rule=True)

question = KriegspielMove(
    QuestionAnnouncement.COMMON,
    chess.Move.from_uci("e2e4"),
)
answer = game.ask_for(question)

print(answer.main_announcement)
print(answer.special_announcement)

game.save_game("game.json")
loaded = BerkeleyGame.load_game("game.json")
```

## Main Concepts

- `BerkeleyGame`: the referee and full hidden board state
- `KriegspielMove`: a player question, either a normal move or `ASK_ANY`
- `KriegspielAnswer`: the referee response, including move outcome, captures, and special announcements

## Links

- PyPI: [kriegspiel](https://pypi.org/project/kriegspiel/)
- Issues: [github.com/Kriegspiel/ks-game/issues](https://github.com/Kriegspiel/ks-game/issues)
