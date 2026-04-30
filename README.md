# kriegspiel

[![PyPI version](https://img.shields.io/pypi/v/kriegspiel.svg?label=PyPI)](https://pypi.org/project/kriegspiel/)

Python game engine for hidden-information Kriegspiel referee rules.

You can try the rules in a live game at [kriegspiel.org](https://kriegspiel.org/).

Current scope:
- Berkeley Kriegspiel
- Berkeley + Any
- Cincinnati
- English
- RAND
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
still use `BerkeleyGame` explicitly as a compatibility wrapper, or pick a ruleset
with `ruleset=...`.

Cincinnati, English, RAND, and Wild 16 also have their own convenience entrypoints:

```python
from kriegspiel import CincinnatiGame, EnglishGame, RandGame, Wild16Game

cincinnati = CincinnatiGame()
print(cincinnati.current_turn_has_pawn_capture)

english = EnglishGame()
print(english.any_rule)

rand = RandGame()
print(rand.current_turn_pawn_try_squares)

wild16 = Wild16Game()
print(wild16.current_turn_pawn_tries)
```

## Main Concepts

- `KriegspielGame`: the neutral public entrypoint for the shared hidden-board engine
- `BerkeleyGame`: backward-compatible Berkeley-named wrapper over `KriegspielGame`
- `CincinnatiGame`: Cincinnati convenience entrypoint with public `NONSENSE` and binary pawn-capture announcements
- `EnglishGame`: English convenience entrypoint with public illegal attempts and one-try `ASK_ANY` handling
- `RandGame`: RAND convenience entrypoint with public rebuffs, pawn-try source-square announcements, typed captures, and promotion notices
- `Wild16Game`: Wild 16 convenience entrypoint over the shared hidden-board engine
- `KriegspielMove`: a player question, either a normal move or `ASK_ANY`
- `KriegspielAnswer`: the referee response, including move outcome, captures, special announcements, and variant-specific public metadata

## Links

- PyPI: [kriegspiel](https://pypi.org/project/kriegspiel/)
- Live site: [kriegspiel.org](https://kriegspiel.org/)
- Issues: [github.com/Kriegspiel/ks-game/issues](https://github.com/Kriegspiel/ks-game/issues)
