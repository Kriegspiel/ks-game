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
from kriegspiel.move import CapturedPieceAnnouncement as CPA
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


def test_common_moves_with_same_value_deduplicate_in_set():
    first = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))
    second = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_promotion_moves_keep_promotion_piece_in_identity():
    queen_promo = KSMove(QA.COMMON, chess.Move(chess.A7, chess.A8, promotion=chess.QUEEN))
    rook_promo = KSMove(QA.COMMON, chess.Move(chess.A7, chess.A8, promotion=chess.ROOK))

    assert queen_promo != rook_promo
    assert len({queen_promo, rook_promo}) == 2


def test_ask_any_never_collides_with_common_moves():
    ask_any = KSMove(QA.ASK_ANY)
    common = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))

    assert ask_any != common
    assert len({ask_any, common}) == 2


def test_move_lt_nonmove_returns_notimplemented():
    move = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))
    assert move.__lt__("not-a-move") is NotImplemented


def test_move_type_errors_include_context():
    with pytest.raises(TypeError, match="question_type must be a QuestionAnnouncement"):
        KSMove("Not a QuestionAnnouncement.")


@pytest.mark.unit
def test_incorrect_answer_type():
    with pytest.raises(TypeError):
        KSAnswer("Not a MainAnnouncement.")


def test_answer_type_errors_include_context():
    with pytest.raises(TypeError, match="main_announcement must be a MainAnnouncement"):
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


@pytest.mark.unit
def test_double_check_validation_count():
    """Test that double check must have exactly two checks."""
    # Valid: exactly 2 checks
    KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(
            SCA.CHECK_DOUBLE,
            [SCA.CHECK_RANK, SCA.CHECK_FILE],
        ),
    )
    
    # Invalid: only 1 check
    with pytest.raises(ValueError, match="Double check must have exactly two check types"):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                [SCA.CHECK_RANK],
            ),
        )
    
    # Invalid: 3 checks
    with pytest.raises(ValueError, match="Double check must have exactly two check types"):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                [SCA.CHECK_RANK, SCA.CHECK_FILE, SCA.CHECK_KNIGHT],
            ),
        )
    
    # Invalid: empty list
    with pytest.raises(ValueError, match="Double check must have exactly two check types"):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                [],
            ),
        )
    
    # Invalid: not a list/tuple
    with pytest.raises(ValueError, match="Double check must have exactly two check types"):
        KSAnswer(
            MA.REGULAR_MOVE,
            special_announcement=(
                SCA.CHECK_DOUBLE,
                "not_a_list",
            ),
        )


def test_SCA_not_tuple_or_SCA():
    with pytest.raises(TypeError):
        KSAnswer(MA.REGULAR_MOVE, special_announcement="Unexpected type.")


def test_captue_at_square():
    a = KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E2)
    assert a.capture_at_square == chess.E2


def test_capture_answer_can_include_public_capture_kind():
    answer = KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.E4,
        captured_piece_announcement=CPA.PAWN,
    )

    assert answer.captured_piece_announcement == CPA.PAWN


def test_capture_answer_rejects_invalid_public_capture_kind():
    with pytest.raises(TypeError, match="captured_piece_announcement must be a CapturedPieceAnnouncement"):
        KSAnswer(
            MA.CAPTURE_DONE,
            capture_at_square=chess.E4,
            captured_piece_announcement="pawn",
        )


def test_non_capture_answer_rejects_public_capture_kind():
    with pytest.raises(TypeError, match="captured_piece_announcement is only valid for CAPTURE_DONE"):
        KSAnswer(MA.REGULAR_MOVE, captured_piece_announcement=CPA.PAWN)


def test_next_turn_pawn_tries_validation():
    answer = KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_tries=2)

    assert answer.next_turn_pawn_tries == 2

    with pytest.raises(TypeError, match="next_turn_pawn_tries must be an integer"):
        KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_tries="2")

    with pytest.raises(ValueError, match="next_turn_pawn_tries must be non-negative"):
        KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_tries=-1)


def test_next_turn_has_pawn_capture_validation():
    answer = KSAnswer(MA.REGULAR_MOVE, next_turn_has_pawn_capture=True)

    assert answer.next_turn_has_pawn_capture is True

    with pytest.raises(TypeError, match="next_turn_has_pawn_capture must be a boolean"):
        KSAnswer(MA.REGULAR_MOVE, next_turn_has_pawn_capture="yes")


def test_next_turn_pawn_try_squares_validation_and_normalization():
    answer = KSAnswer(
        MA.REGULAR_MOVE,
        next_turn_pawn_try_squares=[chess.E4, chess.C2, chess.E4],
    )

    assert answer.next_turn_pawn_try_squares == (chess.C2, chess.E4)

    with pytest.raises(TypeError, match="next_turn_pawn_try_squares must be an iterable"):
        KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_try_squares=chess.E4)

    with pytest.raises(TypeError, match="next_turn_pawn_try_squares must contain only integers"):
        KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_try_squares=[chess.E4, "e5"])

    with pytest.raises(ValueError, match="Invalid pawn try square: 64. Must be 0-63."):
        KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_try_squares=[64])


def test_promotion_announced_validation():
    answer = KSAnswer(MA.REGULAR_MOVE, promotion_announced=True)

    assert answer.promotion_announced is True

    with pytest.raises(TypeError, match="promotion_announced must be a boolean"):
        KSAnswer(MA.REGULAR_MOVE, promotion_announced="yes")


def test_next_turn_pawn_capture_metadata_is_mutually_exclusive():
    with pytest.raises(ValueError, match="Use only one next-turn pawn-capture announcement field"):
        KSAnswer(
            MA.REGULAR_MOVE,
            next_turn_pawn_tries=1,
            next_turn_has_pawn_capture=True,
        )

    with pytest.raises(ValueError, match="Use only one next-turn pawn-capture announcement field"):
        KSAnswer(
            MA.REGULAR_MOVE,
            next_turn_has_pawn_capture=False,
            next_turn_pawn_try_squares=tuple(),
        )


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


def test_scoresheet_snapshot_roundtrip():
    scoresheet = KSSS(chess.BLACK)
    move = KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5))
    answer = KSAnswer(MA.REGULAR_MOVE)
    scoresheet.record_move_own(move, answer)
    scoresheet.record_move_opponent(QA.COMMON, KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E4))

    restored = KSSS.from_snapshot(scoresheet.snapshot())

    assert restored.color == scoresheet.color
    assert restored.moves_own == scoresheet.moves_own
    assert restored.moves_opponent == scoresheet.moves_opponent
    assert restored.last_move_number == scoresheet.last_move_number


def test_scoresheet_from_snapshot_rejects_wrong_type():
    with pytest.raises(TypeError, match="ScoresheetSnapshot"):
        KSSS.from_snapshot("not-a-snapshot")


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


def test_ksanswer_ne_nonanswer():
    assert KSAnswer(MA.REGULAR_MOVE) != object()


def test_equal_double_check_answers_deduplicate_in_set():
    first = KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(SCA.CHECK_DOUBLE, [SCA.CHECK_FILE, SCA.CHECK_KNIGHT]),
    )
    second = KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(SCA.CHECK_DOUBLE, [SCA.CHECK_FILE, SCA.CHECK_KNIGHT]),
    )

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_answers_with_distinct_payloads_stay_distinct():
    capture = KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E4)
    regular = KSAnswer(MA.REGULAR_MOVE)
    file_check = KSAnswer(MA.REGULAR_MOVE, special_announcement=SCA.CHECK_FILE)

    assert capture != regular
    assert regular != file_check
    assert len({capture, regular, file_check}) == 3


def test_answer_lt_nonanswer_returns_notimplemented():
    answer = KSAnswer(MA.REGULAR_MOVE)
    assert answer.__lt__("not-an-answer") is NotImplemented


def test_ksanswer_str_with_double_check_payload():
    answer = KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(SCA.CHECK_DOUBLE, [SCA.CHECK_FILE, SCA.CHECK_KNIGHT]),
    )

    assert str(answer) == (
        "<KriegspielAnswer: MainAnnouncement.REGULAR_MOVE, "
        "capture_at=None, captured_piece=None, special_case=SpecialCaseAnnouncement.CHECK_DOUBLE, "
        "next_turn_pawn_tries=None, "
        "check_1=SpecialCaseAnnouncement.CHECK_FILE, "
        "check_2=SpecialCaseAnnouncement.CHECK_KNIGHT>"
    )


def test_ksanswer_str_with_capture_payload_and_no_double_check():
    answer = KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.E4,
        captured_piece_announcement=CPA.PAWN,
    )

    assert str(answer) == (
        "<KriegspielAnswer: MainAnnouncement.CAPTURE_DONE, "
        "capture_at=e4, captured_piece=CapturedPieceAnnouncement.PAWN, "
        "special_case=SpecialCaseAnnouncement.NONE, next_turn_pawn_tries=None>"
    )


def test_ksanswer_str_with_cincinnati_pawn_capture_payload():
    answer = KSAnswer(
        MA.REGULAR_MOVE,
        next_turn_has_pawn_capture=True,
    )

    assert str(answer) == (
        "<KriegspielAnswer: MainAnnouncement.REGULAR_MOVE, "
        "capture_at=None, captured_piece=None, special_case=SpecialCaseAnnouncement.NONE, "
        "next_turn_pawn_tries=None, next_turn_has_pawn_capture=True>"
    )


def test_ksanswer_str_with_rand_payload():
    answer = KSAnswer(
        MA.REGULAR_MOVE,
        next_turn_pawn_try_squares=(chess.E4,),
        promotion_announced=True,
    )

    assert str(answer) == (
        "<KriegspielAnswer: MainAnnouncement.REGULAR_MOVE, "
        "capture_at=None, captured_piece=None, special_case=SpecialCaseAnnouncement.NONE, "
        "next_turn_pawn_tries=None, next_turn_pawn_try_squares=('e4',), "
        "promotion_announced=True>"
    )


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


def test_ksss_groups_multiple_attempts_into_one_turn():
    scoresheet = KSSS(chess.WHITE)
    illegal_attempt = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E5))
    legal_move = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))

    scoresheet.record_move_own(illegal_attempt, KSAnswer(MA.ILLEGAL_MOVE))
    scoresheet.record_move_own(legal_move, KSAnswer(MA.REGULAR_MOVE))

    assert len(scoresheet.moves_own) == 1
    assert [pair[0] for pair in scoresheet.moves_own[0]] == [illegal_attempt, legal_move]


def test_ksss_opponent_too_detailed_ask():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_opponent(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)), KSAnswer(MA.REGULAR_MOVE))


def test_ksss_opponent_not_enough_details_in_response():
    a = KSSS(chess.BLACK)
    with pytest.raises(ValueError):
        a.record_move_opponent(QA.COMMON, MA.REGULAR_MOVE)
