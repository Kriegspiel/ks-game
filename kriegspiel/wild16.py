# -*- coding: utf-8 -*-

"""Convenience entrypoint for the Wild 16 Kriegspiel ruleset."""

from __future__ import annotations

from kriegspiel.game import KriegspielGame
from kriegspiel.move import KriegspielScoresheet as KSSS
from kriegspiel.rulesets import RULESET_WILD16
from kriegspiel.serialization import load_game_from_json


class Wild16Game(KriegspielGame):
    """Wild 16 convenience wrapper over the shared Berkeley-family engine."""

    def __init__(self):
        super().__init__(ruleset=RULESET_WILD16)

    @classmethod
    def _from_kriegspiel_game(cls, game):
        """Rebuild a Wild16Game wrapper from a validated shared-engine instance."""
        if not isinstance(game, KriegspielGame):
            raise TypeError("game must be a KriegspielGame")
        if game.ruleset_id != RULESET_WILD16:
            raise ValueError("game must use the wild16 ruleset")

        instance = cls()
        instance._board = game._board.copy(stack=True)
        instance._must_use_pawns = game._must_use_pawns
        instance._game_over = game._game_over
        instance._possible_to_ask = list(game.possible_to_ask)
        instance._possible_to_ask_set = set(game.possible_to_ask)
        instance._whites_scoresheet = KSSS.from_snapshot(game._whites_scoresheet.snapshot())
        instance._blacks_scoresheet = KSSS.from_snapshot(game._blacks_scoresheet.snapshot())
        return instance

    _from_berkeley_game = _from_kriegspiel_game

    @classmethod
    def from_snapshot(cls, snapshot):
        """Build a Wild16Game from a validated snapshot."""
        return cls._from_kriegspiel_game(KriegspielGame.from_snapshot(snapshot))

    @classmethod
    def load_game(cls, filename):
        """Load a Wild 16 game from disk."""
        return cls._from_kriegspiel_game(load_game_from_json(filename))
