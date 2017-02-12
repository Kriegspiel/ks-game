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
    assert g.ask_for(chess.Move.from_uci('g6f7')) == (MA.CAPUTRE_DONE, chess.F7, SCA.CHECK)


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
