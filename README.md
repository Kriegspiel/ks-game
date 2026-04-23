# kriegspiel

[![PyPI version](https://badge.fury.io/py/kriegspiel.svg)](https://pypi.org/project/kriegspiel/)

Python game engine for hidden-information Kriegspiel referee rules.

Current scope:
- Berkeley Kriegspiel
- Berkeley + Any
- Wild 16

The package models the referee, not a UI. You interact with it by asking questions as `KriegspielMove` objects and reading `KriegspielAnswer` results.

## Install

```bash
pip install kriegspiel
```

## Quick Start

```python
import chess

from kriegspiel import KriegspielGame, KriegspielMove, QuestionAnnouncement

game = KriegspielGame()

question = KriegspielMove(
    QuestionAnnouncement.COMMON,
    chess.Move.from_uci("e2e4"),
)
answer = game.ask_for(question)

print(answer.main_announcement)
print(answer.special_announcement)

game.save_game("game.json")
loaded = KriegspielGame.load_game("game.json")
```

`KriegspielGame()` defaults to Berkeley + Any for backward compatibility. You can
still use `BerkeleyGame` explicitly, or pick a ruleset with `ruleset=...`.

Wild 16 also has its own convenience entrypoint:

```python
from kriegspiel import Wild16Game

wild16 = Wild16Game()
print(wild16.current_turn_pawn_tries)
```

## Main Concepts

- `KriegspielGame`: the neutral public entrypoint for the shared hidden-board engine
- `BerkeleyGame`: backward-compatible Berkeley-named entrypoint for the same engine
- `Wild16Game`: Wild 16 convenience entrypoint over the shared hidden-board engine
- `KriegspielMove`: a player question, either a normal move or `ASK_ANY`
- `KriegspielAnswer`: the referee response, including move outcome, captures, special announcements, and variant-specific public metadata

## Links

- PyPI: [kriegspiel](https://pypi.org/project/kriegspiel/)
- Issues: [github.com/Kriegspiel/ks-game/issues](https://github.com/Kriegspiel/ks-game/issues)
