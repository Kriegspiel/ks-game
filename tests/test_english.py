# -*- coding: utf-8 -*-

"""English-specific engine and convenience entrypoint tests."""

import os
import tempfile

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.english import EnglishGame
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.move import SpecialCaseAnnouncement as SCA
from kriegspiel.rulesets import RULESET_ENGLISH, resolve_ruleset_policy


def _build_english_any_game():
    game = EnglishGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A5, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._board.set_piece_at(chess.D5, chess.Piece(chess.BISHOP, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def test_english_game_uses_english_ruleset():
    game = EnglishGame()

    assert game.ruleset_id == RULESET_ENGLISH
    assert game.any_rule is True
    assert KSMove(QA.ASK_ANY) in game.possible_to_ask
    assert game.current_turn_has_pawn_capture is None
    assert game.current_turn_pawn_tries is None
    assert game.current_turn_pawn_try_squares is None


def test_english_policy_uses_public_illegal_attempts_and_untyped_captures():
    policy = resolve_ruleset_policy(ruleset=RULESET_ENGLISH)

    assert policy.classify_impossible_common_attempt() == MA.ILLEGAL_MOVE
    assert policy.public_illegal_attempts is True
    assert policy.discard_illegal_attempts is True
    assert policy.typed_capture_announcements is False
    assert policy.announce_promotion is False
    assert policy.release_ask_any_after_failed_pawn_try is True
    assert policy.captured_piece_announcement_for(chess.Piece(chess.PAWN, chess.BLACK)) is None


def test_english_any_no_allows_regular_move_without_public_metadata():
    game = EnglishGame()

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.NO_ANY)
    assert game.must_use_pawns is False
    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4"))) == KSAnswer(MA.REGULAR_MOVE)


def test_english_any_yes_requires_one_pawn_try_before_other_moves():
    game = _build_english_any_game()
    rook_move = KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)
    assert game.must_use_pawns is True
    assert game.ask_for(rook_move) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)
    assert game.must_use_pawns is True


def test_english_failed_pawn_try_releases_any_obligation():
    game = _build_english_any_game()
    empty_pawn_try = KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))
    rook_move = KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)
    assert game.ask_for(empty_pawn_try) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game.must_use_pawns is False
    assert rook_move in game.possible_to_ask
    assert empty_pawn_try not in game.possible_to_ask
    assert game.ask_for(rook_move) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.A5)


def test_english_legal_pawn_capture_after_any_completes_move():
    game = _build_english_any_game()

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)
    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.D5))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.D5,
    )


def test_english_capture_announces_square_but_not_captured_kind():
    game = _build_english_any_game()

    result = game.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5)))

    assert result == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.A5)
    assert result.captured_piece_announcement is None


def test_english_public_illegal_attempt_is_visible_to_opponent():
    game = EnglishGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A3, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game._blacks_scoresheet.moves_opponent[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)


def test_english_impossible_common_attempt_is_public_illegal_outside_any_obligation():
    game = EnglishGame()
    impossible = KSMove(QA.COMMON, chess.Move.from_uci("e2e5"))

    assert game.ask_for(impossible) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game._whites_scoresheet.moves_own[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)
    assert game._blacks_scoresheet.moves_opponent[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)


def test_english_promotion_is_silent():
    game = EnglishGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.A4, chess.Piece(chess.KING, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.H7, chess.H8, promotion=chess.QUEEN))) == KSAnswer(
        MA.REGULAR_MOVE
    )


def test_english_stalemate_remains_draw():
    game = EnglishGame()
    game._board.clear()
    game._board.set_piece_at(chess.F7, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.G5, chess.Piece(chess.QUEEN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.G5, chess.G6))) == KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=SCA.DRAW_STALEMATE,
    )


def test_english_from_snapshot_returns_variant_instance():
    game = EnglishGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    restored = EnglishGame.from_snapshot(game.snapshot())

    assert isinstance(restored, EnglishGame)
    assert restored.ruleset_id == RULESET_ENGLISH
    assert restored._board.fen() == game._board.fen()


def test_english_from_snapshot_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with pytest.raises(ValueError, match="english ruleset"):
        EnglishGame.from_snapshot(game.snapshot())


def test_english_private_helper_rejects_non_game():
    with pytest.raises(TypeError, match="KriegspielGame"):
        EnglishGame._from_kriegspiel_game("not-a-game")


def test_english_load_game_returns_variant_instance():
    game = EnglishGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        restored = EnglishGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, EnglishGame)
    assert restored.ruleset_id == RULESET_ENGLISH
    assert restored._board.fen() == game._board.fen()


def test_english_load_game_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        with pytest.raises(ValueError, match="english ruleset"):
            EnglishGame.load_game(filename)
    finally:
        os.unlink(filename)
