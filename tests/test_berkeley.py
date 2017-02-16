# -*- coding: utf-8 -*-

import pytest

from ks_game.berkeley import chess
from ks_game.berkeley import BerkeleyGame
from ks_game.berkeley import MoveAnnouncement as MA
from ks_game.berkeley import AnyRuleAnnouncement as ARA
from ks_game.berkeley import SpecialCaseAnnouncement as SCA


def test_white_e2e4():
    g = BerkeleyGame()
    assert g.ask_for(chess.Move.from_uci('e2e4')) == (MA.REGULAR_MOVE, None, None)


def test_black_regular_move():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    assert g.ask_for(chess.Move.from_uci('e7e5')) == (MA.REGULAR_MOVE, None, None)


def test_white_any_true():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    assert g.ask_for(ARA.ASK_ANY) == (ARA.HAS_ANY, None, None)


def test_black_any_true():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    assert g.ask_for(ARA.ASK_ANY) == (ARA.HAS_ANY, None, None)


def test_black_illegal_after_any_true():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    # Legal in chess, but illegal after ask 'for any'
    assert g.ask_for(chess.Move.from_uci('d8d7')) == (MA.ILLEGAL_MOVE, None, None)


def test_black_legal_after_any_true():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    # Capture by pawn after ANY
    assert g.ask_for(chess.Move.from_uci('d5e4')) == (MA.CAPUTRE_DONE, chess.E4, None)


def test_white_any_false():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    assert g.ask_for(ARA.ASK_ANY) == (ARA.NO_ANY, None, None)


def test_white_capture_and_check():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    g.ask_for(ARA.ASK_ANY)
    assert g.ask_for(chess.Move.from_uci('g6f7')) == (MA.CAPUTRE_DONE, chess.F7, SCA.CHECK_SHORT_DIAGONAL)


def test_black_from_check_false():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('g6f7'))
    assert g.ask_for(chess.Move.from_uci('e8e7')) == (MA.ILLEGAL_MOVE, None, None)


def test_black_from_check_true_and_capture():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('g6f7'))
    g.ask_for(chess.Move.from_uci('e8e7'))
    assert g.ask_for(chess.Move.from_uci('e8f7')) == (MA.CAPUTRE_DONE, chess.F7, None)


def test_black_any_true_en_passant():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('g6f7'))
    g.ask_for(chess.Move.from_uci('e8e7'))
    g.ask_for(chess.Move.from_uci('e8f7'))
    g.ask_for(chess.Move.from_uci('g1f3'))
    g.ask_for(chess.Move.from_uci('e4e3'))
    g.ask_for(chess.Move.from_uci('f3g1'))
    g.ask_for(chess.Move.from_uci('e5e4'))
    g.ask_for(chess.Move.from_uci('f2f4'))
    assert g.ask_for(ARA.ASK_ANY) == (ARA.HAS_ANY, None, None)


def test_black_capture_en_passant():
    g = BerkeleyGame()
    g.ask_for(chess.Move.from_uci('e2e4'))
    g.ask_for(chess.Move.from_uci('e7e5'))
    g.ask_for(chess.Move.from_uci('d1h5'))
    g.ask_for(chess.Move.from_uci('d7d5'))
    g.ask_for(chess.Move.from_uci('h5g6'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('d5e4'))
    g.ask_for(ARA.ASK_ANY)
    g.ask_for(chess.Move.from_uci('g6f7'))
    g.ask_for(chess.Move.from_uci('e8e7'))
    g.ask_for(chess.Move.from_uci('e8f7'))
    g.ask_for(chess.Move.from_uci('g1f3'))
    g.ask_for(chess.Move.from_uci('e4e3'))
    g.ask_for(chess.Move.from_uci('f3g1'))
    g.ask_for(chess.Move.from_uci('e5e4'))
    g.ask_for(chess.Move.from_uci('f2f4'))
    g.ask_for(ARA.ASK_ANY)
    assert g.ask_for(chess.Move.from_uci('e4f3')) == (MA.CAPUTRE_DONE, chess.F4, None)


def test_check_short_diagonal():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.C1)) == (MA.REGULAR_MOVE, None, SCA.CHECK_SHORT_DIAGONAL)


def test_check_file():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.A1)) == (MA.REGULAR_MOVE, None, SCA.CHECK_FILE)


def test_check_rank():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.D3)) == (MA.REGULAR_MOVE, None, SCA.CHECK_RANK)


def test_check_long_diagonal():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.D6)) == (MA.REGULAR_MOVE, None, SCA.CHECK_LONG_DIAGONAL)


def test_check_knight():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g.ask_for(chess.Move(chess.B2, chess.A3))
    g.board.set_piece_at(chess.C3, chess.Piece(chess.KNIGHT, chess.BLACK))
    assert g.ask_for(chess.Move(chess.C3, chess.B5)) == (MA.REGULAR_MOVE, None, SCA.CHECK_KNIGHT)


def test_check_double():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.BLACK))
    g.board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g.ask_for(chess.Move(chess.C2, chess.B2))
    assert g.ask_for(chess.Move(chess.D2, chess.C4)) == (MA.REGULAR_MOVE, None, SCA.CHECK_DOUBLE)
