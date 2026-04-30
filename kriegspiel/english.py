# -*- coding: utf-8 -*-

"""Convenience entrypoint for the English Kriegspiel ruleset."""

from __future__ import annotations

from kriegspiel.game import KriegspielGame
from kriegspiel.move import KriegspielScoresheet as KSSS
from kriegspiel.rulesets import RULESET_ENGLISH
from kriegspiel.serialization import load_game_from_json


class EnglishGame(KriegspielGame):
    """English convenience wrapper over the shared hidden-board engine."""

    def __init__(self):
        super().__init__(ruleset=RULESET_ENGLISH)

    @classmethod
    def _from_kriegspiel_game(cls, game):
        """Rebuild an EnglishGame wrapper from a validated shared-engine instance."""
        if not isinstance(game, KriegspielGame):
            raise TypeError("game must be a KriegspielGame")
        if game.ruleset_id != RULESET_ENGLISH:
            raise ValueError("game must use the english ruleset")

        instance = cls()
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
        """Build an EnglishGame from a validated snapshot."""
        return cls._from_kriegspiel_game(KriegspielGame.from_snapshot(snapshot))

    @classmethod
    def load_game(cls, filename):
        """Load an English game from disk."""
        return cls._from_kriegspiel_game(load_game_from_json(filename))
