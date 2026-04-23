# -*- coding: utf-8 -*-

"""Generic public entrypoint for the shared Kriegspiel engine."""

from __future__ import annotations

from kriegspiel.berkeley import BerkeleyGame
from kriegspiel.move import KriegspielScoresheet as KSSS
from kriegspiel.serialization import load_game_from_json


class KriegspielGame(BerkeleyGame):
    """Neutral public entrypoint for the shared hidden-board Kriegspiel engine.

    This class uses the same engine as ``BerkeleyGame`` but exposes it through a
    generic name that fits multiple rulesets. The historical Berkeley-named
    class remains available for backward compatibility.
    """

    def __init__(self, any_rule=None, ruleset=None):
        super().__init__(any_rule=any_rule, ruleset=ruleset)

    @classmethod
    def _from_berkeley_game(cls, game):
        """Rebuild a KriegspielGame from a validated shared-engine instance."""
        if not isinstance(game, BerkeleyGame):
            raise TypeError("game must be a BerkeleyGame")

        instance = cls(ruleset=game.ruleset_id)
        instance._board = game._board.copy(stack=True)
        instance._must_use_pawns = game._must_use_pawns
        instance._game_over = game._game_over
        instance._possible_to_ask = list(game.possible_to_ask)
        instance._possible_to_ask_set = set(game.possible_to_ask)
        instance._whites_scoresheet = KSSS.from_snapshot(game._whites_scoresheet.snapshot())
        instance._blacks_scoresheet = KSSS.from_snapshot(game._blacks_scoresheet.snapshot())
        return instance

    @classmethod
    def from_snapshot(cls, snapshot):
        """Build a KriegspielGame from a validated snapshot."""
        return cls._from_berkeley_game(BerkeleyGame.from_snapshot(snapshot))

    @classmethod
    def load_game(cls, filename):
        """Load a shared-engine Kriegspiel game from disk."""
        return cls._from_berkeley_game(load_game_from_json(filename))
