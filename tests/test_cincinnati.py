# -*- coding: utf-8 -*-

"""Cincinnati-specific engine and convenience entrypoint tests."""

import os
import tempfile

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.cincinnati import CincinnatiGame
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.rulesets import RULESET_CINCINNATI, resolve_ruleset_policy


def _build_hidden_blocker_game():
    game = CincinnatiGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def test_cincinnati_game_uses_cincinnati_ruleset():
    g = CincinnatiGame()

    assert g.ruleset_id == RULESET_CINCINNATI
    assert g.any_rule is False
    assert KSMove(QA.ASK_ANY) not in g.possible_to_ask
    assert g.current_turn_has_pawn_capture is False
    assert g.current_turn_pawn_tries is None


def test_cincinnati_policy_uses_public_nonsense_and_binary_pawn_capture():
    policy = resolve_ruleset_policy(ruleset=RULESET_CINCINNATI)

    assert policy.classify_impossible_common_attempt() == MA.NONSENSE
    assert policy.public_illegal_attempts is True
    assert policy.discard_illegal_attempts is True
    assert policy.typed_capture_announcements is True


def test_cincinnati_illegal_attempt_is_public_to_opponent():
    g = _build_hidden_blocker_game()
    move = KSMove(QA.COMMON, chess.Move(chess.C1, chess.H6))

    result = g.ask_for(move)

    assert result == KSAnswer(MA.ILLEGAL_MOVE)
    assert len(g._whites_scoresheet.moves_own) == 1
    assert g._whites_scoresheet.moves_own[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)
    assert g._blacks_scoresheet.moves_opponent[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)


def test_cincinnati_repeated_hidden_illegal_attempt_becomes_nonsense():
    g = _build_hidden_blocker_game()
    move = KSMove(QA.COMMON, chess.Move(chess.C1, chess.H6))

    assert move in g.possible_to_ask
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)
    assert g.ask_for(move) == KSAnswer(MA.NONSENSE)
    assert len(g._whites_scoresheet.moves_own[0]) == 2
    assert g._blacks_scoresheet.moves_opponent[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)
    assert g._blacks_scoresheet.moves_opponent[0][1][1] == KSAnswer(MA.NONSENSE)


def test_cincinnati_impossible_attempt_from_empty_square_is_nonsense():
    g = CincinnatiGame()

    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E3, chess.E4))) == KSAnswer(MA.NONSENSE)


def test_cincinnati_completed_move_announces_binary_pawn_capture():
    g = CincinnatiGame()

    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))

    assert result == KSAnswer(MA.REGULAR_MOVE, next_turn_has_pawn_capture=True)
    assert g.current_turn_has_pawn_capture is True


def test_cincinnati_completed_move_can_announce_no_pawn_capture():
    g = CincinnatiGame()

    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))

    assert result == KSAnswer(MA.REGULAR_MOVE, next_turn_has_pawn_capture=False)
    assert g.current_turn_has_pawn_capture is False


def test_cincinnati_capture_announces_pawn_kind():
    g = CincinnatiGame()
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
        next_turn_has_pawn_capture=False,
    )


def test_cincinnati_pawn_capture_announcement_ignores_captures_that_do_not_escape_check():
    g = CincinnatiGame()
    g._board.clear()
    g._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.set_piece_at(chess.E3, chess.Piece(chess.BISHOP, chess.BLACK))
    g._generate_possible_to_ask_list()

    assert g.current_turn_has_pawn_capture is False


def test_cincinnati_ask_any_is_not_supported():
    g = CincinnatiGame()

    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_cincinnati_from_snapshot_returns_variant_instance():
    g = CincinnatiGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    restored = CincinnatiGame.from_snapshot(g.snapshot())

    assert isinstance(restored, CincinnatiGame)
    assert restored.ruleset_id == RULESET_CINCINNATI
    assert restored._board.fen() == g._board.fen()


def test_cincinnati_from_snapshot_rejects_other_ruleset():
    g = BerkeleyGame(any_rule=False)

    with pytest.raises(ValueError, match="cincinnati ruleset"):
        CincinnatiGame.from_snapshot(g.snapshot())


def test_cincinnati_private_helper_rejects_non_game():
    with pytest.raises(TypeError, match="KriegspielGame"):
        CincinnatiGame._from_kriegspiel_game("not-a-game")


def test_cincinnati_load_game_returns_variant_instance():
    g = CincinnatiGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        g.save_game(filename)
        restored = CincinnatiGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, CincinnatiGame)
    assert restored.ruleset_id == RULESET_CINCINNATI
    assert restored._board.fen() == g._board.fen()


def test_cincinnati_load_game_rejects_other_ruleset():
    g = BerkeleyGame(any_rule=False)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        g.save_game(filename)
        with pytest.raises(ValueError, match="cincinnati ruleset"):
            CincinnatiGame.load_game(filename)
    finally:
        os.unlink(filename)
