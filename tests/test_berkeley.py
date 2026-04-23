# -*- coding: utf-8 -*-
"""
Integration tests for the Berkeley Kriegspiel game engine.

This module contains comprehensive tests for the BerkeleyGame class,
covering game mechanics, rule enforcement, and edge cases.
Test categories:
- Basic moves and game flow
- Kriegspiel-specific rules (ANY questions, pawn captures)
- Special cases (checks, checkmates, draws)
- Edge cases (long games, complex positions)
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
from kriegspiel.rulesets import RULESET_BERKELEY
from kriegspiel.rulesets import RULESET_BERKELEY_ANY
from kriegspiel.rulesets import RULESET_WILD16
from kriegspiel.rulesets import resolve_ruleset_policy
from kriegspiel.snapshot import BerkeleyGameSnapshot


def _build_hidden_blocker_wild16_game():
    game = BerkeleyGame(ruleset=RULESET_WILD16)
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


@pytest.mark.integration
def test_white_e2e4():
    g = BerkeleyGame()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4))) == KSAnswer(MA.REGULAR_MOVE)


def test_black_regular_move():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5))) == KSAnswer(MA.REGULAR_MOVE)


@pytest.mark.rules
def test_white_any_true():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)


@pytest.mark.rules
def test_black_any_true():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)


def test_explicit_ruleset_can_disable_ask_any():
    g = BerkeleyGame(ruleset=RULESET_BERKELEY)

    assert g.ruleset_id == RULESET_BERKELEY
    assert g.any_rule is False
    assert KSMove(QA.ASK_ANY) not in g.possible_to_ask


def test_conflicting_ruleset_arguments_are_rejected():
    with pytest.raises(ValueError, match="conflicts"):
        BerkeleyGame(ruleset=RULESET_BERKELEY, any_rule=True)


def test_unknown_ruleset_is_rejected():
    with pytest.raises(ValueError, match="Unsupported ruleset"):
        BerkeleyGame(ruleset="unknown_variant")


def test_explicit_ruleset_can_enable_wild16():
    g = BerkeleyGame(ruleset=RULESET_WILD16)

    assert g.ruleset_id == RULESET_WILD16
    assert g.any_rule is False
    assert KSMove(QA.ASK_ANY) not in g.possible_to_ask
    assert g.current_turn_pawn_tries == 0


def test_ruleset_policy_returns_none_for_non_special_question():
    policy = resolve_ruleset_policy(ruleset=RULESET_BERKELEY_ANY)

    assert policy.handle_special_question(BerkeleyGame(), KSMove(QA.NONE)) is None


def test_ruleset_policy_rejects_ask_any_when_disabled():
    policy = resolve_ruleset_policy(ruleset=RULESET_BERKELEY)

    assert policy.handle_special_question(BerkeleyGame(any_rule=False), KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_wild16_policy_uses_private_illegal_moves():
    policy = resolve_ruleset_policy(ruleset=RULESET_WILD16)

    assert policy.classify_impossible_common_attempt() == MA.ILLEGAL_MOVE
    assert policy.public_illegal_attempts is False
    assert policy.discard_illegal_attempts is False


def test_wild16_illegal_attempt_is_private_to_mover():
    g = BerkeleyGame(ruleset=RULESET_WILD16)

    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E5)))

    assert result == KSAnswer(MA.ILLEGAL_MOVE)
    assert len(g._whites_scoresheet.moves_own) == 1
    assert g._whites_scoresheet.moves_own[0][0][1] == KSAnswer(MA.ILLEGAL_MOVE)
    assert g._blacks_scoresheet.moves_opponent == []


def test_wild16_hidden_illegal_attempt_stays_repeatable():
    g = _build_hidden_blocker_wild16_game()
    move = KSMove(QA.COMMON, chess.Move(chess.C1, chess.H6))

    assert move in g.possible_to_ask
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)
    assert len(g._whites_scoresheet.moves_own[0]) == 2
    assert g._blacks_scoresheet.moves_opponent == []


def test_wild16_completed_move_announces_next_turn_pawn_tries():
    g = BerkeleyGame(ruleset=RULESET_WILD16)

    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    result = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))

    assert result == KSAnswer(MA.REGULAR_MOVE, next_turn_pawn_tries=1)
    assert g.current_turn_pawn_tries == 1


def test_wild16_capture_announces_pawn_kind():
    g = BerkeleyGame(ruleset=RULESET_WILD16)
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
        next_turn_pawn_tries=0,
    )


def test_wild16_pawn_try_count_ignores_captures_that_do_not_escape_check():
    g = BerkeleyGame(ruleset=RULESET_WILD16)
    g._board.clear()
    g._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.set_piece_at(chess.E3, chess.Piece(chess.BISHOP, chess.BLACK))
    g._generate_possible_to_ask_list()

    assert g.current_turn_pawn_tries == 0


def test_wild16_ask_any_is_not_supported():
    g = BerkeleyGame(ruleset=RULESET_WILD16)

    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_black_illegal_after_any_true():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    # Legal in chess, but illegal after ask 'for any'
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.D7))) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_black_legal_after_any_true():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    # Capture by pawn after ANY
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4))) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.E4)


def test_white_any_false():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.NO_ANY)


def test_white_capture_and_check():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G6, chess.F7))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.F7,
        special_announcement=SCA.CHECK_SHORT_DIAGONAL,
    )


def test_black_from_check_false():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G6, chess.F7)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.E7))) == KSAnswer(MA.ILLEGAL_MOVE)


def test_black_from_check_true_and_capture():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G6, chess.F7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.E7)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F7))) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.F7)


def test_black_any_true_en_passant():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G6, chess.F7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.E7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.E3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E5, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F2, chess.F4)))
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)


def test_black_capture_en_passant():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G6, chess.F7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.E7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F7)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.E3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E5, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F2, chess.F4)))
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.F3))) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.F4)


def test_white_capture_en_passant():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E4, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F7, chess.F5)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E5, chess.F6))) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.F5)


@pytest.mark.rules
def test_check_short_diagonal():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A3)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.C1))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_SHORT_DIAGONAL
    )


def test_check_file():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A3)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.A1))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_FILE
    )


def test_check_rank():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A3)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.D3))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_RANK
    )


def test_check_long_diagonal():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A3)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.D6))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_LONG_DIAGONAL
    )


def test_check_knight():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A3)))
    g._board.set_piece_at(chess.C3, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C3, chess.B5))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_KNIGHT
    )


def test_check_double():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C2, chess.B2)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C4))) == KSAnswer(
        MA.REGULAR_MOVE,
        special_announcement=(SCA.CHECK_DOUBLE, [SCA.CHECK_RANK, SCA.CHECK_KNIGHT]),
    )


def test_check_double_check_1():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C2, chess.B2)))
    res = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C4)))
    assert res.check_1 in [SCA.CHECK_RANK, SCA.CHECK_KNIGHT]


def test_check_double_check_2():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C2, chess.B2)))
    res = g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C4)))
    assert res.check_2 in [SCA.CHECK_RANK, SCA.CHECK_KNIGHT]


def test_promotion_check_long():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A7, chess.A8, promotion=chess.QUEEN))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_LONG_DIAGONAL
    )


def test_impossible_to_promotion_without_piece_spesification():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A7, chess.A8))) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


@pytest.mark.edge_case
@pytest.mark.slow
def test_200_reversible_moves():
    g = BerkeleyGame()
    for _ in range(499):
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.DRAW_TOOMANYREVERSIBLEMOVES
    )


def test_five_fold_is_not_draw():
    # 1
    g = BerkeleyGame()
    # 2
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 3
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 4
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 5
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8))) == KSAnswer(MA.REGULAR_MOVE)


def test_five_fold_then_checkmate():
    # 1
    g = BerkeleyGame()
    # 2
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 3
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 4
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # 5
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    # School checkmate
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.F3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B8, chess.A6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F1, chess.C4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A6, chess.B8)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.F7))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.F7,
        special_announcement=SCA.CHECKMATE_WHITE_WINS,
    )


@pytest.mark.edge_case
@pytest.mark.slow
def test_75_moves_is_not_draw():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
    g._generate_possible_to_ask_list()

    white_king_sq = chess.A1
    for _ in range(4):
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H8, chess.G8)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H8)))
    # 14
    for _ in range(4):
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F8)))
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.G8)))
    # 28
    for _ in range(4):
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.E8)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F8)))
    for _ in range(4):
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.D8)))
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.E8)))
    # 56
    for _ in range(4):
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.C8)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C8, chess.D8)))
    for _ in range(4):
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C8, chess.B8)))
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B8, chess.C8)))
    # 84
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B8, chess.C8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A2, chess.A1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C8, chess.D8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.E8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A2, chess.A1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.B2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.G8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H8)))
    # 96
    white_king_sq = chess.A2
    for _ in range(4):
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H8, chess.G8)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H8)))
    for _ in range(4):
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F8)))
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.G8)))
    for _ in range(4):
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.E8)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq + 1)))
        white_king_sq += 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.F8)))
    for _ in range(2):
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.D8)))
        white_king_sq -= 1
        g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.E8)))
    # 146
    white_king_sq -= 1
    g.ask_for(KSMove(QA.COMMON, chess.Move(white_king_sq, white_king_sq - 1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E8, chess.D8)))
    # 148
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C2, chess.C3)))
    # 149
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D8, chess.D7))) == KSAnswer(MA.REGULAR_MOVE)


@pytest.mark.rules
def test_stalemate():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A7))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.DRAW_STALEMATE
    )


@pytest.mark.rules
def test_white_wins():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g._board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A8))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECKMATE_WHITE_WINS
    )


def test_black_wins():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A8))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECKMATE_BLACK_WINS
    )


def test_draw_insufficient():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A8, chess.Piece(chess.QUEEN, chess.WHITE))
    g._board.set_piece_at(chess.F7, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.G4, chess.Piece(chess.BISHOP, chess.WHITE))
    g._board.set_piece_at(chess.D4, chess.Piece(chess.KING, chess.BLACK))
    g._generate_possible_to_ask_list()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A8, chess.D5)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D4, chess.D5))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.D5,
        special_announcement=SCA.DRAW_INSUFFICIENT,
    )


def test_impossible_ask_move_from_empty_square():
    g = BerkeleyGame()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E3, chess.E4))) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_illegal_to_castling_through_check():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F1, chess.C4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.C5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.H3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F2, chess.F4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B8, chess.A6)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E1, chess.G1))) == KSAnswer(MA.ILLEGAL_MOVE)


def test_castling():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F1, chess.C4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.C5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.H3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H6)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E1, chess.G1))) == KSAnswer(MA.REGULAR_MOVE)


def test_impossible_ask_castling_after_move():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F1, chess.C4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.C5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.H3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F2, chess.F4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F7, chess.F5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E1, chess.E2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C5, chess.F8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H8, chess.G8)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E1, chess.G1))) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_35_possibilities_in_init():
    g = BerkeleyGame()
    assert len(g.possible_to_ask) == 35


def test_ask_for_any_only_once():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_impossible_ask_nonpawnmoves_after_askany():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.ASK_ANY))
    assert (KSMove(QA.COMMON, chess.Move(chess.B1, chess.C3)) in g.possible_to_ask) is False


def test_always_possible_to_ask_any():
    g = BerkeleyGame()
    assert (KSMove(QA.ASK_ANY) in g.possible_to_ask) is True


def test_ask_any_not_possible_when_variant_disables_it():
    g = BerkeleyGame(any_rule=False)
    assert KSMove(QA.ASK_ANY) not in g.possible_to_ask


def test_possible_capture_with_promotion():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert KSMove(QA.COMMON, chess.Move(chess.A7, chess.B8, promotion=chess.BISHOP)) in g.possible_to_ask


def test_12_possibilities_with_pawn_capture_and_promotion():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()
    assert len(g.possible_to_ask) == 12


def test_repeated_generation_keeps_promotion_capture_options_stable():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.WHITE))
    g._board.set_piece_at(chess.H1, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    g._generate_possible_to_ask_list()

    expected = set(g.possible_to_ask)

    for _ in range(3):
        g._generate_possible_to_ask_list()
        assert set(g.possible_to_ask) == expected


def test_no_legal_moves_after_gameover():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
    g._board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    # Checkmate
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A8)))
    assert len(g.possible_to_ask) == 0


def test_ask_same_twice():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.F3)))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.F3))) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_hidden_enemy_blocker_still_allows_the_question_to_be_asked():
    g = BerkeleyGame(any_rule=False)
    g._board.clear()
    g._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    g._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    g._generate_possible_to_ask_list()

    move = KSMove(QA.COMMON, chess.Move(chess.C1, chess.E3))

    assert move in g.possible_to_ask
    assert g.ask_for(move) == KSAnswer(MA.ILLEGAL_MOVE)


def test_no_possible_pawn_capture_after_false_any():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.F3))) not in g.possible_to_ask


def test_was_illegal_and_not_possible_after_any():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    illegal_move = KSMove(QA.COMMON, chess.Move(chess.G6, chess.G8))
    g.ask_for(illegal_move)
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(illegal_move) not in g.possible_to_ask


def test_impossible_ask_same_move_twice():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D5, chess.E4)))
    illegal_move = KSMove(QA.COMMON, chess.Move(chess.G6, chess.G8))
    g.ask_for(illegal_move)
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.ask_for(illegal_move) not in g.possible_to_ask


@pytest.mark.parametrize(
    "what, result",
    [
        (KSMove(QA.ASK_ANY), True),
        (KSMove(QA.COMMON, chess.Move(chess.E2, chess.E1)), False),
    ],
)
def test_possible_to_ask(what, result):
    g = BerkeleyGame()
    assert g.is_possible_to_ask(what) == result


def test_castling_rights_control_possible_to_ask_membership():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F1, chess.C4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F8, chess.C5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.H3)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.H6)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F2, chess.F4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F7, chess.F5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E1, chess.E2)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.C5, chess.F8)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E1)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H8, chess.G8)))

    assert KSMove(QA.COMMON, chess.Move(chess.E1, chess.G1)) not in g.possible_to_ask


def test_discard_possible_to_ask_is_noop_for_absent_move():
    g = BerkeleyGame()
    impossible = KSMove(QA.COMMON, chess.Move(chess.E2, chess.E1))
    before = set(g.possible_to_ask)

    g._discard_possible_to_ask(impossible)

    assert set(g.possible_to_ask) == before


def test_initial_game_is_not_over():
    g = BerkeleyGame()
    assert g.game_over == False


def test_mate_is_game_over():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    # Stalemate
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A7)))
    assert g.game_over == True


def test_mate_is_game_over_2():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    g._generate_possible_to_ask_list()
    # Stalemate
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A7)))
    assert g.is_game_over() == True


def test_may_not_use_pawns_at_initial_state():
    g = BerkeleyGame()
    assert g.must_use_pawns == False


def test_must_use_pawns_after_positive_ask_any():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))
    assert g.must_use_pawns == True


def test_check_short_diagonal_upper_left_quadrant():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B8, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.WHITE))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.G1, chess.Piece(chess.QUEEN, chess.BLACK))
    g._board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.A7))) == KSAnswer(
        MA.REGULAR_MOVE, special_announcement=SCA.CHECK_SHORT_DIAGONAL
    )


def test_promotion_capture_check():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.B2, chess.Piece(chess.PAWN, chess.BLACK))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.QUEEN, chess.WHITE))
    g._board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A1, promotion=chess.QUEEN))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.A1,
        special_announcement=SCA.CHECK_LONG_DIAGONAL,
    )


def test_promotion_capture_draw():
    g = BerkeleyGame()
    g._board.clear()
    g._board.set_piece_at(chess.B8, chess.Piece(chess.KING, chess.BLACK))
    g._board.set_piece_at(chess.B2, chess.Piece(chess.PAWN, chess.BLACK))
    g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.WHITE))
    g._board.set_piece_at(chess.A1, chess.Piece(chess.QUEEN, chess.WHITE))
    g._board.turn = chess.BLACK
    g._generate_possible_to_ask_list()
    assert g.ask_for(KSMove(QA.COMMON, chess.Move(chess.B2, chess.A1, promotion=chess.BISHOP))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.A1,
        special_announcement=SCA.DRAW_INSUFFICIENT,
    )


def test_ask_for_bad_type():
    g = BerkeleyGame()
    with pytest.raises(TypeError):
        g.ask_for("Not a KSMove.")


def test_white_starts():
    g = BerkeleyGame()
    assert g.turn == chess.WHITE


def test_if_berkeley_wo_any():
    g = BerkeleyGame(any_rule=False)
    assert g.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


def test_snapshot_roundtrip_preserves_ruleset_and_questions():
    g = BerkeleyGame(ruleset=RULESET_BERKELEY_ANY)
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))

    restored = BerkeleyGame.from_snapshot(g.snapshot())

    assert restored.ruleset_id == g.ruleset_id
    assert restored.any_rule == g.any_rule
    assert restored.turn == g.turn
    assert set(restored.possible_to_ask) == set(g.possible_to_ask)


def test_snapshot_roundtrip_can_rebuild_legacy_possible_to_ask():
    g = BerkeleyGame()
    snapshot = g.snapshot()
    legacy_snapshot = BerkeleyGameSnapshot(
        ruleset_id=snapshot.ruleset_id,
        any_rule=snapshot.any_rule,
        board_fen=snapshot.board_fen,
        move_stack=snapshot.move_stack,
        must_use_pawns=snapshot.must_use_pawns,
        game_over=snapshot.game_over,
        possible_to_ask=None,
        white_scoresheet=snapshot.white_scoresheet,
        black_scoresheet=snapshot.black_scoresheet,
    )

    restored = BerkeleyGame.from_snapshot(legacy_snapshot)

    assert restored.ruleset_id == g.ruleset_id
    assert set(restored.possible_to_ask) == set(g.possible_to_ask)


def test_snapshot_roundtrip_can_rebuild_legacy_must_use_pawns_state():
    g = BerkeleyGame()
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E2, chess.E4)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.E7, chess.E5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D1, chess.H5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.D7, chess.D5)))
    g.ask_for(KSMove(QA.COMMON, chess.Move(chess.H5, chess.G6)))
    g.ask_for(KSMove(QA.ASK_ANY))

    snapshot = g.snapshot()
    legacy_snapshot = BerkeleyGameSnapshot(
        ruleset_id=snapshot.ruleset_id,
        any_rule=snapshot.any_rule,
        board_fen=snapshot.board_fen,
        move_stack=snapshot.move_stack,
        must_use_pawns=snapshot.must_use_pawns,
        game_over=snapshot.game_over,
        possible_to_ask=None,
        white_scoresheet=snapshot.white_scoresheet,
        black_scoresheet=snapshot.black_scoresheet,
    )

    restored = BerkeleyGame.from_snapshot(legacy_snapshot)

    assert restored.must_use_pawns is True
    assert set(restored.possible_to_ask) == set(g._generate_possible_pawn_captures())


def test_from_snapshot_rejects_wrong_type():
    with pytest.raises(TypeError, match="BerkeleyGameSnapshot"):
        BerkeleyGame.from_snapshot("not-a-snapshot")


def test_ask_for_reports_unsupported_question_type_once_it_is_marked_possible():
    g = BerkeleyGame()
    strange_question = KSMove(QA.NONE)
    g._possible_to_ask.append(strange_question)
    g._possible_to_ask_set.add(strange_question)

    with pytest.raises(ValueError, match="Unsupported question type"):
        g._ask_for(strange_question)
