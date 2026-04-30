# -*- coding: utf-8 -*-

"""CrazyKrieg-specific engine and convenience entrypoint tests."""

import os
import tempfile

import chess.variant
import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.crazykrieg import CrazyKriegGame
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.move import SpecialCaseAnnouncement as SCA
from kriegspiel.rulesets import RULESET_CRAZYKRIEG, resolve_ruleset_policy
from kriegspiel.snapshot import PublicReserveSummary, ReserveSideSummary


def _reset_board(game):
    game._board.clear()
    game._board.pockets[chess.WHITE].reset()
    game._board.pockets[chess.BLACK].reset()


def _build_crazy_any_game():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A5, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._board.set_piece_at(chess.D5, chess.Piece(chess.BISHOP, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def test_crazykrieg_game_uses_crazyhouse_board_and_policy():
    game = CrazyKriegGame()
    policy = resolve_ruleset_policy(ruleset=RULESET_CRAZYKRIEG)

    assert game.ruleset_id == RULESET_CRAZYKRIEG
    assert isinstance(game._board, chess.variant.CrazyhouseBoard)
    assert game.any_rule is True
    assert KSMove(QA.ASK_ANY) in game.possible_to_ask
    assert game.current_turn_has_pawn_capture is None
    assert game.current_turn_pawn_tries is None
    assert game.current_turn_pawn_try_squares is None
    assert policy.public_illegal_attempts is True
    assert policy.exact_capture_announcements is True
    assert policy.announce_drops is True


def test_crazykrieg_capture_adds_exact_public_reserve_identity():
    game = CrazyKriegGame()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4"))) == KSAnswer(MA.REGULAR_MOVE)
    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5"))) == KSAnswer(MA.REGULAR_MOVE)
    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5"))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.D5,
        captured_piece_announcement=CPA.PAWN,
    )
    assert game.public_reserve_summary == PublicReserveSummary(
        white=ReserveSideSummary(pawns=1),
        black=ReserveSideSummary(),
    )


def test_crazykrieg_drop_announces_piece_type_but_not_square_to_opponent():
    game = CrazyKriegGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("g8f6")))

    drop = KSMove(QA.COMMON, chess.Move.from_uci("P@e3"))
    answer = KSAnswer(MA.REGULAR_MOVE, dropped_piece_announcement=CPA.PAWN)

    assert drop in game.possible_to_ask
    assert game.ask_for(drop) == answer
    assert game.public_reserve_summary.white == ReserveSideSummary()
    assert game._blacks_scoresheet.moves_opponent[-1][-1] == (QA.COMMON, answer)


def test_crazykrieg_drop_on_hidden_occupied_square_is_public_illegal_and_discarded():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.E3, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._board.pockets[chess.WHITE].add(chess.PAWN)
    game._generate_possible_to_ask_list()
    drop = KSMove(QA.COMMON, chess.Move.from_uci("P@e3"))

    assert drop in game.possible_to_ask
    assert game.ask_for(drop) == KSAnswer(MA.ILLEGAL_MOVE)
    assert drop not in game.possible_to_ask
    assert game._blacks_scoresheet.moves_opponent[0][0] == (QA.COMMON, KSAnswer(MA.ILLEGAL_MOVE))


def test_crazykrieg_capture_of_promoted_pawn_enters_reserve_as_pawn():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.QUEEN, chess.WHITE), promoted=True)
    game._board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
    game._board.turn = chess.BLACK
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d8e8"))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.E8,
        captured_piece_announcement=CPA.PAWN,
    )
    assert game.public_reserve_summary.black == ReserveSideSummary(pawns=1)


def test_crazykrieg_exact_non_pawn_capture_identity_is_public():
    game = _build_crazy_any_game()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.A5,
        captured_piece_announcement=CPA.KNIGHT,
    )
    assert game.public_reserve_summary.white == ReserveSideSummary(knights=1)


def test_crazykrieg_any_yes_requires_one_pawn_try_then_releases_after_failed_try():
    game = _build_crazy_any_game()
    rook_move = KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))
    empty_pawn_try = KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)
    assert game.must_use_pawns is True
    assert game.ask_for(rook_move) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)
    assert game.must_use_pawns is True
    assert game.ask_for(empty_pawn_try) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game.must_use_pawns is False
    assert rook_move in game.possible_to_ask


def test_crazykrieg_drop_can_give_check_without_revealing_square():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.pockets[chess.WHITE].add(chess.KNIGHT)
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("N@f7"))) == KSAnswer(
        MA.REGULAR_MOVE,
        dropped_piece_announcement=CPA.KNIGHT,
        special_announcement=SCA.CHECK_KNIGHT,
    )


def test_crazykrieg_reserve_material_prevents_insufficient_material_draw():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.pockets[chess.WHITE].add(chess.PAWN)
    game._generate_possible_to_ask_list()

    assert game.is_game_over() is False


def test_crazykrieg_empty_reserve_keeps_insufficient_material_draw():
    game = CrazyKriegGame()
    _reset_board(game)
    game._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.is_game_over() is True


def test_crazykrieg_from_snapshot_returns_variant_instance():
    game = CrazyKriegGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5")))

    restored = CrazyKriegGame.from_snapshot(game.snapshot())

    assert isinstance(restored, CrazyKriegGame)
    assert restored.ruleset_id == RULESET_CRAZYKRIEG
    assert restored._board.fen() == game._board.fen()
    assert restored.public_reserve_summary == game.public_reserve_summary


def test_crazykrieg_from_snapshot_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with pytest.raises(ValueError, match="crazykrieg ruleset"):
        CrazyKriegGame.from_snapshot(game.snapshot())


def test_crazykrieg_private_helper_rejects_non_game():
    with pytest.raises(TypeError, match="KriegspielGame"):
        CrazyKriegGame._from_kriegspiel_game("not-a-game")


def test_crazykrieg_load_game_returns_variant_instance():
    game = CrazyKriegGame()
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5")))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        restored = CrazyKriegGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, CrazyKriegGame)
    assert restored.ruleset_id == RULESET_CRAZYKRIEG
    assert restored._board.fen() == game._board.fen()
    assert restored.public_reserve_summary == game.public_reserve_summary


def test_crazykrieg_load_game_rejects_other_ruleset():
    game = BerkeleyGame(any_rule=False)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        with pytest.raises(ValueError, match="crazykrieg ruleset"):
            CrazyKriegGame.load_game(filename)
    finally:
        os.unlink(filename)
