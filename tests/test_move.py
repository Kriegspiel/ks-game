# -*- coding: utf-8 -*-
"""
Unit tests for Kriegspiel data structures and move handling.

This module contains tests for the core data structures used in Kriegspiel:
- KriegspielMove: Player questions and move requests
- KriegspielAnswer: Referee responses  
- KriegspielScoresheet: Game history tracking

These are primarily unit tests focusing on data validation,
type checking, and individual component behavior.
"""

import pytest

from kriegspiel.berkeley import chess
from kriegspiel.berkeley import BerkeleyGame

from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA

from kriegspiel.move import KriegspielScoresheet as KSSS


@pytest.mark.unit
def test_incorrect_move_type():
    with pytest.raises(TypeError):
        KSMove("Not a QuestionAnnouncement.")


@pytest.mark.unit
def test_incorrect_chess_move_type():
    with pytest.raises(TypeError):
        KSMove(QA.COMMON, "Not a chess.Move.")


def test_move_sorting_first():
    g = BerkeleyGame()
    assert sorted(g.possible_to_ask)[0] == KSMove(QA.ASK_ANY)


def test_move_sorting_last():
    g = BerkeleyGame()
    assert sorted(g.possible_to_ask)[-1] == KSMove(QA.COMMON, chess.Move(chess.H2, chess.H4))


def test_move_ne_nonmove():
    assert KSMove(QA.ASK_ANY) != "A nonmove."


@pytest.mark.unit
def test_incorrect_answer_type():
    with pytest.raises(TypeError):
        KSAnswer("Not a MainAnnouncement.")


def test_capture_with_no_square_id():
    with pytest.raises(TypeError):
        KSAnswer(MA.CAPTURE_DONE, capture_at_square="Not a square id.")


def test_double_check_but_not_checks():
    with pytest.raises(TypeError):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(SCA.CHECK_DOUBLE, ["Not a check.", SCA.CHECK_KNIGHT]),
        )


def test_double_check_but_not_single_checks():
    with pytest.raises(TypeError):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                [SCA.CHECK_DOUBLE, SCA.CHECK_KNIGHT],
            ),
        )


def test_if_tuple_but_nondouble_check():
    with pytest.raises(TypeError):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                "Nondouble check.",
                [SCA.CHECK_DOUBLE, SCA.CHECK_KNIGHT],
            ),
        )


def test_valid_double_check():
    a = KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(
            SCA.CHECK_DOUBLE,
            [SCA.CHECK_SHORT_DIAGONAL, SCA.CHECK_KNIGHT],
        ),
    )
    assert a.check_2 == SCA.CHECK_KNIGHT


def test_SCA_not_tuple_or_SCA():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement="Unexpected type.")


def test_captue_at_square():
    a = KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E2)
    assert a.capture_at_square == chess.E2


@pytest.mark.unit
def test_capture_square_range_validation():
    """Test that capture squares must be within valid range (0-63)."""
    # Valid squares (0-63) should work
    KSAnswer(MA.CAPTURE_DONE, capture_at_square=0)   # A1
    KSAnswer(MA.CAPTURE_DONE, capture_at_square=63)  # H8
    KSAnswer(MA.CAPTURE_DONE, capture_at_square=32)  # Middle square
    
    # Invalid squares should raise ValueError
    with pytest.raises(ValueError, match="Invalid square number: -1. Must be 0-63."):
        KSAnswer(MA.CAPTURE_DONE, capture_at_square=-1)
    
    with pytest.raises(ValueError, match="Invalid square number: 64. Must be 0-63."):
        KSAnswer(MA.CAPTURE_DONE, capture_at_square=64)
    
    with pytest.raises(ValueError, match="Invalid square number: 100. Must be 0-63."):
        KSAnswer(MA.CAPTURE_DONE, capture_at_square=100)


def test_special_annoucement():
    a = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    assert a.special_announcement == SCA.CHECK_RANK


def test_ksanswer_ne():
    a = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    b = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    ne = a != b
    assert ne == False


def test_ksanswer_lt():
    a = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    b = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    ne = a < b
    assert ne == False


def test_ksanswer_hash():
    a = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    b = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK)
    hash_a = hash(a)
    hash_b = hash(b)
    assert hash_a == hash_b


@pytest.mark.unit
def test_ksss_empty_own_moves():
    a = KSSS(chess.WHITE)
    assert len(a.moves_own) == 0


@pytest.mark.unit
def test_ksss_opponents_moves():
    a = KSSS(chess.WHITE)
    a.record_move_opponent(
        QA.COMMON,
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                [SCA.CHECK_SHORT_DIAGONAL, SCA.CHECK_FILE],
            ),
        ),
    )
    assert len(a.moves_opponent) == 1


def test_ksss_color():
    a = KSSS(chess.BLACK)
    assert a.color == chess.BLACK


def test_ksss_color_no_setter():
    a = KSSS(chess.BLACK)
    with pytest.raises(AttributeError):
        a.color = chess.WHITE


def test_ksss_own_chess_move():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_own(chess.Move(chess.E2, chess.E4), KSAnswer(MA.REGULAR_MOVE))


def test_ksss_own_wrong_answer():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_own(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)), MA.REGULAR_MOVE)


def test_ksss_opponent_too_detailed_ask():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_opponent(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)), KSAnswer(MA.REGULAR_MOVE))


def test_ksss_opponent_not_enough_details_in_response():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_opponent(QA.COMMON, MA.REGULAR_MOVE)
