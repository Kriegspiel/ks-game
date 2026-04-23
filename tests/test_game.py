# -*- coding: utf-8 -*-

"""Tests for the neutral shared-engine public API."""

import os
import tempfile

import chess
import pytest

from kriegspiel import BerkeleyGame
from kriegspiel import KriegspielGame
from kriegspiel import KriegspielMove as KSMove
from kriegspiel import MainAnnouncement as MA
from kriegspiel import QuestionAnnouncement as QA
from kriegspiel import Wild16Game
from kriegspiel.rulesets import RULESET_BERKELEY
from kriegspiel.rulesets import RULESET_BERKELEY_ANY
from kriegspiel.snapshot import ScoresheetSnapshot
from kriegspiel.snapshot import move_stack_from_scoresheets
from kriegspiel.move import KriegspielAnswer as KSAnswer


def test_generic_game_defaults_to_berkeley_any():
    game = KriegspielGame()

    assert game.ruleset_id == RULESET_BERKELEY_ANY
    assert game.any_rule is True


def test_generic_game_from_snapshot_returns_generic_class():
    game = KriegspielGame(ruleset=RULESET_BERKELEY)
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))

    restored = KriegspielGame.from_snapshot(game.snapshot())

    assert isinstance(restored, KriegspielGame)
    assert restored.__class__ is KriegspielGame
    assert restored.ruleset_id == RULESET_BERKELEY
    assert restored._board.fen() == game._board.fen()


def test_generic_game_load_game_returns_generic_class():
    game = KriegspielGame(ruleset=RULESET_BERKELEY)
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        restored = KriegspielGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, KriegspielGame)
    assert restored.__class__ is KriegspielGame
    assert restored._board.fen() == game._board.fen()


def test_generic_game_helper_rejects_non_game():
    with pytest.raises(TypeError, match="BerkeleyGame"):
        KriegspielGame._from_berkeley_game("not-a-game")


def test_berkeley_name_remains_available():
    game = BerkeleyGame(any_rule=False)

    assert isinstance(game, BerkeleyGame)
    assert game.ruleset_id == RULESET_BERKELEY


def test_move_stack_from_scoresheets_handles_black_only_turns():
    black_move = KSMove(QA.COMMON, chess.Move.from_uci("e7e5"))
    black_answer = KSAnswer(MA.REGULAR_MOVE)
    white_scoresheet = ScoresheetSnapshot(
        color=chess.WHITE,
        moves_own=tuple(),
        moves_opponent=tuple(),
        last_move_number=0,
    )
    black_scoresheet = ScoresheetSnapshot(
        color=chess.BLACK,
        moves_own=(((black_move, black_answer),),),
        moves_opponent=tuple(),
        last_move_number=1,
    )

    assert move_stack_from_scoresheets(white_scoresheet, black_scoresheet) == ("e7e5",)


def test_package_root_exports_variant_entrypoints():
    assert KriegspielGame.__name__ == "KriegspielGame"
    assert BerkeleyGame.__name__ == "BerkeleyGame"
    assert Wild16Game.__name__ == "Wild16Game"
