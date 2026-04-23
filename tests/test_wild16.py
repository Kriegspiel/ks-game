# -*- coding: utf-8 -*-

"""Wild 16-specific engine and convenience entrypoint tests."""

import os
import tempfile

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.rulesets import RULESET_WILD16, resolve_ruleset_policy
from kriegspiel.wild16 import Wild16Game


def _build_hidden_blocker_game():
    game = Wild16Game()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def test_wild16_game_uses_wild16_ruleset():
    g = Wild16Game()

    assert g.ruleset_id == RULESET_WILD16
    assert g.any_rule is False
    assert KSMove(QA.ASK_ANY) not in g.possible_to_ask
    assert g.current_turn_pawn_tries == 0


def test_wild16_policy_uses_private_illegal_moves():
    policy = resolve_ruleset_policy(ruleset=RULESET_WILD16)

    assert policy.classify_impossible_common_attempt() == MA.ILLEGAL_MOVE
    assert policy.public_illegal_attempts is False
    assert policy.discard_illegal_attempts is False


def test_wild16_illegal_attempt_is_private_to_mover():
    g = Wild16Game()

    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E5)))

    assert result == KSAnswer(MA.ILLEGAL_MOVE)
    assert len(g._whites_scoresheet.moves_own) == 1
    assert g._whites_scoresheet.moves_own[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)
    assert g._blacks_scoresheet.moves_opponent == []


def test_wild16_hidden_illegal_attempt_stays_repeatable():
    g = _build_hidden_blocker_game()
    move = KSMove(QA.COMMON, chess.Move(chess.C1, chess.H6))

    assert move in g.possible_to_ask
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)
    assert len(g._whites_scoresheet.moves_own[0]) == 2
    assert g._blacks_scoresheet.moves_opponent == []


def test_wild16_completed_move_announces_next_turn_pawn_tries():
    g = Wild16Game()

    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))

    assert result == KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_tries=1)
    assert g.current_turn_pawn_tries == 1


def test_wild16_capture_announces_pawn_kind():
    g = Wild16Game()
    g._board.clear()
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))
    g._generate_possible_to_ask_list()

    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.D5))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.D5,
        captured_piece_announcement=CPA.PAWN,
        next_turn_pawn_tries=0,
    )


def test_wild16_pawn_try_count_ignores_captures_that_do_not_escape_check():
    g = Wild16Game()
    g._board.clear()
    g._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.set_piece_at(chess.E3, chess.Piece(chess.BISHOP, chess.BLACK))
    g._generate_possible_to_ask_list()

    assert g.current_turn_pawn_tries == 0


def test_wild16_ask_any_is_not_supported():
    g = Wild16Game()

    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_wild16_from_snapshot_returns_variant_instance():
    g = Wild16Game()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    restored = Wild16Game.from_snapshot(g.snapshot())

    assert isinstance(restored, Wild16Game)
    assert restored.ruleset_id == RULESET_WILD16
    assert restored._board.fen() == g._board.fen()


def test_wild16_from_snapshot_rejects_other_ruleset():
    g = BerkeleyGame(any_rule=False)

    with pytest.raises(ValueError, match="wild16 ruleset"):
        Wild16Game.from_snapshot(g.snapshot())


def test_wild16_private_helper_rejects_non_game():
    with pytest.raises(TypeError, match="BerkeleyGame"):
        Wild16Game._from_berkeley_game("not-a-game")


def test_wild16_load_game_returns_variant_instance():
    g = Wild16Game()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        g.save_game(filename)
        restored = Wild16Game.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, Wild16Game)
    assert restored.ruleset_id == RULESET_WILD16
    assert restored._board.fen() == g._board.fen()


def test_wild16_load_game_rejects_other_ruleset():
    g = BerkeleyGame(any_rule=False)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        g.save_game(filename)
        with pytest.raises(ValueError, match="wild16 ruleset"):
            Wild16Game.load_game(filename)
    finally:
        os.unlink(filename)
