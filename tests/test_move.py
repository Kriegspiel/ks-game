# -*- coding: utf-8 -*-

import pytest

from kriegspiel.berkeley import chess
from kriegspiel.berkeley import BerkeleyGame

from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA


def test_incorrect_move_type():
    with pytest.raises(TypeError):
        KSMove('Not a QuestionAnnouncement.')


def test_incorrect_chess_move_type():
    with pytest.raises(TypeError):
        KSMove(QA.COMMON, 'Not a chess.Move.')


def test_move_sorting_first():
    g = BerkeleyGame()
    assert sorted(g.possible_to_ask)[0] == KSMove(QA.ASK_ANY)


def test_move_sorting_last():
    g = BerkeleyGame()
    assert sorted(g.possible_to_ask)[-1] == KSMove(QA.COMMON, chess.Move(chess.H2, chess.H4))


def test_move_ne_nonmove():
    assert KSMove(QA.ASK_ANY) != 'A nonmove.'


def test_incorrect_answer_type():
    with pytest.raises(TypeError):
        KSAnswer('Not a MainAnnouncement.')


def test_capture_with_no_square_id():
    with pytest.raises(TypeError):
        KSAnswer(MA.CAPTURE_DONE, capture_at_square='Not a square id.')


def test_double_check_but_not_checks():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement=(SCA.CHECK_DOUBLE, ['Not a check.', SCA.CHECK_KNIGHT]))


def test_double_check_but_not_single_checks():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement=(SCA.CHECK_DOUBLE, [SCA.CHECK_DOUBLE, SCA.CHECK_KNIGHT]))


def test_if_tuple_but_nondouble_check():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement=('Nondouble check.', [SCA.CHECK_DOUBLE, SCA.CHECK_KNIGHT]))


def test_SCA_not_tuple_or_SCA():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement='Unexpected type.')


def test_captue_at_square():
    a = KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E2)
    assert KSAnswer.capture_at_square == chess.E2


def test_captue_at_square():
    a = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    assert KSAnswer.special_announcement == SCA.CHECK_RANK
