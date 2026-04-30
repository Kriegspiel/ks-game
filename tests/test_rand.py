# -*- coding: utf-8 -*-

"""RAND-specific engine and convenience entrypoint tests."""

import os
import tempfile

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.move import SpecialCaseAnnouncement as SCA
from kriegspiel.rand import RandGame
from kriegspiel.rulesets import RULESET_RAND, resolve_ruleset_policy


def _build_rand_pawn_try_game():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.C4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.F5, chess.Piece(chess.ROOK, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def test_rand_game_uses_rand_ruleset():
    game = RandGame()

    assert game.ruleset_id == RULESET_RAND
    assert game.any_rule is False
    assert KSMove(QA.ASK_ANY) not in game.possible_to_ask
    assert game.current_turn_pawn_try_squares == tuple()
    assert game.current_turn_has_pawn_capture is None
    assert game.current_turn_pawn_tries is None


def test_rand_policy_uses_public_rebuffs_typed_captures_and_promotion_notices():
    policy = resolve_ruleset_policy(ruleset=RULESET_RAND)

    assert policy.classify_impossible_common_attempt() == MA.NONSENSE
    assert policy.public_illegal_attempts is True
    assert policy.discard_illegal_attempts is True
    assert policy.typed_capture_announcements is True
    assert policy.announce_promotion is True
    assert policy.stalemate_loses is True


def test_rand_announces_only_pawn_source_squares_with_legal_capture_tries():
    game = _build_rand_pawn_try_game()
    legal_try = KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))
    unannounced_pawn_try = KSMove(QA.COMMON, chess.Move(chess.C4, chess.D5))

    assert game.current_turn_pawn_try_squares == (chess.E4,)
    assert legal_try in game.possible_to_ask
    assert unannounced_pawn_try not in game.possible_to_ask
    assert game.ask_for(unannounced_pawn_try) == KSAnswer(MA.NONSENSE)


def test_rand_completed_move_announces_next_turn_pawn_try_squares():
    game = RandGame()

    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    result = game.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))

    assert result == KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_try_squares=(chess.E4,))
    assert game.current_turn_pawn_try_squares == (chess.E4,)


def test_rand_capture_announces_square_piece_kind_and_next_pawn_try_squares():
    game = _build_rand_pawn_try_game()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.F5,
        captured_piece_announcement=CPA.PIECE,
        next_turn_pawn_try_squares=tuple(),
    )


def test_rand_public_rebuffs_are_visible_to_opponent_and_repeated_try_is_nonsense():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A3, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()

    first_try = KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))

    assert game.ask_for(first_try) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game.ask_for(first_try) == KSAnswer(MA.NONSENSE)
    assert len(game._whites_scoresheet.moves_own[0]) == 2
    assert len(game._blacks_scoresheet.moves_opponent[0]) == 2
    assert [answer.main_announcement for _question, answer in game._blacks_scoresheet.moves_opponent[0]] == [
        MA.ILLEGAL_MOVE,
        MA.NONSENSE,
    ]


def test_rand_ask_any_is_not_supported():
    game = RandGame()

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_rand_en_passant_uses_capturable_pawn_source_and_captured_pawn_square():
    game = RandGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.H7, chess.H6)))
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.E5)))
    result = game.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))

    assert result.next_turn_pawn_try_squares == (chess.E5,)
    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E5, chess.D6))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.D5,
        captured_piece_announcement=CPA.PAWN,
        next_turn_pawn_try_squares=tuple(),
    )


def test_rand_pawn_try_squares_only_include_captures_that_escape_check():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.C2, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.D3, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game._board.is_check()
    assert game.current_turn_pawn_try_squares == (chess.C2,)
    assert KSMove(QA.COMMON, chess.Move(chess.C2, chess.D3)) in game.possible_to_ask


def test_rand_ignores_pawn_captures_that_do_not_escape_check():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    game._board.set_piece_at(chess.E3, chess.Piece(chess.BISHOP, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game._board.is_check()
    assert game.current_turn_pawn_try_squares == tuple()
    assert KSMove(QA.COMMON, chess.Move(chess.D2, chess.E3)) not in game.possible_to_ask


def test_rand_announces_promotion_without_piece_type_or_square():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.A4, chess.Piece(chess.KING, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.H7, chess.H8, promotion=chess.QUEEN))) == KSAnswer(
        MA.REGULAR_MOVE,
        promotion_announced=True,
        next_turn_pawn_try_squares=tuple(),
    )


def test_rand_announces_capture_and_promotion_together():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.F3, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.turn = chess.BLACK
    game._generate_possible_to_ask_list()

    assert game.current_turn_pawn_try_squares == (chess.D2,)
    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C1, promotion=chess.QUEEN))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.C1,
        captured_piece_announcement=CPA.PIECE,
        promotion_announced=True,
        next_turn_pawn_try_squares=tuple(),
    )


def test_rand_ladder_stalemate_is_loss_for_stalemated_side():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.F7, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.G5, chess.Piece(chess.QUEEN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.G5, chess.G6))) == KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=SCA.STALEMATE_WHITE_WINS,
    )


def test_rand_from_snapshot_returns_variant_instance():
    game = RandGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    restored = RandGame.from_snapshot(game.snapshot())

    assert isinstance(restored, RandGame)
    assert restored.ruleset_id == RULESET_RAND
    assert restored._board.fen() == game._board.fen()


def test_rand_from_snapshot_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with pytest.raises(ValueError, match="rand ruleset"):
        RandGame.from_snapshot(game.snapshot())


def test_rand_private_helper_rejects_non_game():
    with pytest.raises(TypeError, match="KriegspielGame"):
        RandGame._from_kriegspiel_game("not-a-game")


def test_rand_load_game_returns_variant_instance():
    game = RandGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        restored = RandGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, RandGame)
    assert restored.ruleset_id == RULESET_RAND
    assert restored._board.fen() == game._board.fen()


def test_rand_load_game_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        with pytest.raises(ValueError, match="rand ruleset"):
            RandGame.load_game(filename)
    finally:
        os.unlink(filename)
