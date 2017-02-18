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
    assert g.ask_for(chess.Move.from_uci('d8d7')) == (MA.IMPOSSIBLE_TO_ASK, None, None)


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
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.C1)) == (MA.REGULAR_MOVE, None, SCA.CHECK_SHORT_DIAGONAL)


def test_check_file():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.A1)) == (MA.REGULAR_MOVE, None, SCA.CHECK_FILE)


def test_check_rank():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.D3)) == (MA.REGULAR_MOVE, None, SCA.CHECK_RANK)


def test_check_long_diagonal():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.B2, chess.A3))
    assert g.ask_for(chess.Move(chess.D1, chess.D6)) == (MA.REGULAR_MOVE, None, SCA.CHECK_LONG_DIAGONAL)


def test_check_knight():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.B2, chess.A3))
    g.board.set_piece_at(chess.C3, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.C3, chess.B5)) == (MA.REGULAR_MOVE, None, SCA.CHECK_KNIGHT)


def test_check_double():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.BLACK))
    g.board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.C2, chess.B2))
    assert g.ask_for(chess.Move(chess.D2, chess.C4)) == (MA.REGULAR_MOVE, None, SCA.CHECK_DOUBLE)


def test_promotion_check_long():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g.board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.A7, chess.A8, promotion=chess.QUEEN)) == (MA.REGULAR_MOVE, None, SCA.CHECK_LONG_DIAGONAL)


def test_impossible_to_promotion_without_piece_spesification():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g.board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.A7, chess.A8)) == (MA.IMPOSSIBLE_TO_ASK, None, None)


def test_five_fold_draw():
    # 1
    g = BerkeleyGame()
    # 2
    g.ask_for(chess.Move(chess.G1, chess.F3))
    g.ask_for(chess.Move(chess.G8, chess.F6))
    g.ask_for(chess.Move(chess.F3, chess.G1))
    g.ask_for(chess.Move(chess.F6, chess.G8))
    # 3
    g.ask_for(chess.Move(chess.G1, chess.F3))
    g.ask_for(chess.Move(chess.G8, chess.F6))
    g.ask_for(chess.Move(chess.F3, chess.G1))
    g.ask_for(chess.Move(chess.F6, chess.G8))
    # 4
    g.ask_for(chess.Move(chess.G1, chess.F3))
    g.ask_for(chess.Move(chess.G8, chess.F6))
    g.ask_for(chess.Move(chess.F3, chess.G1))
    g.ask_for(chess.Move(chess.F6, chess.G8))
    # 5
    g.ask_for(chess.Move(chess.G1, chess.F3))
    g.ask_for(chess.Move(chess.G8, chess.F6))
    g.ask_for(chess.Move(chess.F3, chess.G1))
    assert g.ask_for(chess.Move(chess.F6, chess.G8)) == (MA.REGULAR_MOVE, None, SCA.DRAW_FIVEFOLD)


def test_75_moves_draw():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
    g._generate_possible_to_ask_list()

    white_king_sq = chess.A1
    for i in range(4):
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.H8, chess.G8))
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.G8, chess.H8))
    # 14
    for i in range(4):
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.G8, chess.F8))
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.F8, chess.G8))
    # 28
    for i in range(4):
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.F8, chess.E8))
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.E8, chess.F8))
    for i in range(4):
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.E8, chess.D8))
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.D8, chess.E8))
    # 56
    for i in range(4):
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.D8, chess.C8))
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.C8, chess.D8))
    for i in range(4):
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.C8, chess.B8))
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.B8, chess.C8))
    # 84
    g.ask_for(chess.Move(chess.A1, chess.A2))
    g.ask_for(chess.Move(chess.B8, chess.C8))
    g.ask_for(chess.Move(chess.A2, chess.A1))
    g.ask_for(chess.Move(chess.C8, chess.D8))
    g.ask_for(chess.Move(chess.A1, chess.A2))
    g.ask_for(chess.Move(chess.D8, chess.E8))
    g.ask_for(chess.Move(chess.A2, chess.A1))
    g.ask_for(chess.Move(chess.E8, chess.F8))
    g.ask_for(chess.Move(chess.A1, chess.B2))
    g.ask_for(chess.Move(chess.F8, chess.G8))
    g.ask_for(chess.Move(chess.B2, chess.A2))
    g.ask_for(chess.Move(chess.G8, chess.H8))
    # 96
    white_king_sq = chess.A2
    for i in range(4):
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.H8, chess.G8))
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.G8, chess.H8))
    for i in range(4):
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.G8, chess.F8))
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.F8, chess.G8))
    for i in range(4):
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.F8, chess.E8))
        g.ask_for(chess.Move(white_king_sq, white_king_sq + 1))
        white_king_sq += 1
        g.ask_for(chess.Move(chess.E8, chess.F8))
    for i in range(2):
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.E8, chess.D8))
        white_king_sq -= 1
        g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
        g.ask_for(chess.Move(chess.D8, chess.E8))
    # 146
    white_king_sq -= 1
    g.ask_for(chess.Move(white_king_sq, white_king_sq - 1))
    g.ask_for(chess.Move(chess.E8, chess.D8))
    # 148
    g.ask_for(chess.Move(chess.C2, chess.C3))
    # 149
    assert g.ask_for(chess.Move(chess.D8, chess.D7)) == (MA.REGULAR_MOVE, None, SCA.DRAW_SEVENTYFIVE)


def test_stalemate():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.A1, chess.A7)) == (MA.REGULAR_MOVE, None, SCA.DRAW_STALEMATE)


def test_white_wins():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g.board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.WHITE))
    g.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.A1, chess.A8)) == (MA.REGULAR_MOVE, None, SCA.CHECKMATE_WHITE_WINS)


def test_black_wins():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.BLACK))
    g.board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.BLACK))
    g.board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.BLACK))
    g.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g.board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    assert g.ask_for(chess.Move(chess.A1, chess.A8)) == (MA.REGULAR_MOVE, None, SCA.CHECKMATE_BLACK_WINS)


def test_draw_insufficient():
    g = BerkeleyGame()
    g.board.clear()
    g.board.set_piece_at(chess.A8, chess.Piece(chess.QUEEN, chess.WHITE))
    g.board.set_piece_at(chess.F7, chess.Piece(chess.KING, chess.WHITE))
    g.board.set_piece_at(chess.G4, chess.Piece(chess.BISHOP, chess.WHITE))
    g.board.set_piece_at(chess.D4, chess.Piece(chess.KING, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(chess.Move(chess.A8, chess.D5))
    assert g.ask_for(chess.Move(chess.D4, chess.D5)) == (MA.CAPUTRE_DONE, chess.D5, SCA.DRAW_INSUFFICIENT)


def test_impossible_ask_move_from_empty_square():
    g = BerkeleyGame()
    assert g.ask_for(chess.Move(chess.E3, chess.E4)) == (MA.IMPOSSIBLE_TO_ASK, None, None)


def test_illegal_to_castling_through_check():
    g = BerkeleyGame()
    g.ask_for(chess.Move(chess.E2, chess.E4))
    g.ask_for(chess.Move(chess.E7, chess.E5))
    g.ask_for(chess.Move(chess.F1, chess.C4))
    g.ask_for(chess.Move(chess.F8, chess.C5))
    g.ask_for(chess.Move(chess.G1, chess.H3))
    g.ask_for(chess.Move(chess.G8, chess.H6))
    g.ask_for(chess.Move(chess.F2, chess.F4))
    g.ask_for(chess.Move(chess.B8, chess.A6))
    assert g.ask_for(chess.Move(chess.E1, chess.G1)) == (MA.ILLEGAL_MOVE, None, None)


def test_castling():
    g = BerkeleyGame()
    g.ask_for(chess.Move(chess.E2, chess.E4))
    g.ask_for(chess.Move(chess.E7, chess.E5))
    g.ask_for(chess.Move(chess.F1, chess.C4))
    g.ask_for(chess.Move(chess.F8, chess.C5))
    g.ask_for(chess.Move(chess.G1, chess.H3))
    g.ask_for(chess.Move(chess.G8, chess.H6))
    assert g.ask_for(chess.Move(chess.E1, chess.G1)) == (MA.REGULAR_MOVE, None, None)


def test_impossible_ask_castling_after_move():
    g = BerkeleyGame()
    g.ask_for(chess.Move(chess.E2, chess.E4))
    g.ask_for(chess.Move(chess.E7, chess.E5))
    g.ask_for(chess.Move(chess.F1, chess.C4))
    g.ask_for(chess.Move(chess.F8, chess.C5))
    g.ask_for(chess.Move(chess.G1, chess.H3))
    g.ask_for(chess.Move(chess.G8, chess.H6))
    g.ask_for(chess.Move(chess.F2, chess.F4))
    g.ask_for(chess.Move(chess.F7, chess.F5))
    g.ask_for(chess.Move(chess.E1, chess.E2))
    g.ask_for(chess.Move(chess.C5, chess.F8))
    assert g.ask_for(chess.Move(chess.E1, chess.G1)) == (MA.IMPOSSIBLE_TO_ASK, None, None)


def test_35_possibilities_in_init():
    g = BerkeleyGame()
    assert len(g.possible_to_ask) == 35


def test_ask_for_any_only_once():
    g = BerkeleyGame()
    g.ask_for(ARA.ASK_ANY)
    assert g.ask_for(ARA.ASK_ANY) == (MA.IMPOSSIBLE_TO_ASK, None, None)


def test_impossible_ask_nonpawnmoves_after_askany():
    g = BerkeleyGame()
    g.ask_for(chess.Move(chess.E2, chess.E4))
    g.ask_for(chess.Move(chess.D7, chess.D5))
    g.ask_for(ARA.ASK_ANY)
    assert (chess.Move(chess.B1, chess.C3) in g.possible_to_ask) is False
