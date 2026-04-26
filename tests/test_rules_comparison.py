# -*- coding: utf-8 -*-

"""Tests that mirror the public rules-comparison table."""

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.cincinnati import CincinnatiGame
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.wild16 import Wild16Game


def _build_rules_comparison_game(game):
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A5, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._board.set_piece_at(chess.D5, chess.Piece(chess.BISHOP, chess.BLACK))
    game._board.set_piece_at(chess.F5, chess.Piece(chess.ROOK, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def _piece_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))


def _left_pawn_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.E4, chess.D5))


def _right_pawn_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))


def _build_promotion_capture_game(game):
    game._board.clear()
    game._board.set_piece_at(chess.F3, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.turn = chess.BLACK
    game._generate_possible_to_ask_list()
    return game


def _promotion_capture_moves():
    return {
        KSMove(QA.COMMON, chess.Move(chess.D2, chess.C1, promotion=promotion))
        for promotion in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
    }


@pytest.mark.rules
def test_rules_comparison_position_announces_binary_vs_counted_pawn_captures():
    berkeley_any = _build_rules_comparison_game(BerkeleyGame())
    berkeley = _build_rules_comparison_game(BerkeleyGame(any_rule=False))
    cincinnati = _build_rules_comparison_game(CincinnatiGame())
    wild16 = _build_rules_comparison_game(Wild16Game())

    assert KSMove(QA.ASK_ANY) in berkeley_any.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in berkeley.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in cincinnati.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in wild16.possible_to_ask

    assert berkeley_any.current_turn_has_pawn_capture is None
    assert berkeley_any.current_turn_pawn_tries is None
    assert berkeley.current_turn_has_pawn_capture is None
    assert berkeley.current_turn_pawn_tries is None
    assert cincinnati.current_turn_has_pawn_capture is True
    assert cincinnati.current_turn_pawn_tries is None
    assert wild16.current_turn_has_pawn_capture is None
    assert wild16.current_turn_pawn_tries == 2


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected_has_pawn_capture", "expected_pawn_tries"),
    [
        pytest.param(BerkeleyGame(), None, None, id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), None, None, id="berkeley"),
        pytest.param(CincinnatiGame(), True, None, id="cincinnati"),
        pytest.param(Wild16Game(), None, 1, id="wild16"),
    ],
)
def test_rules_comparison_promotion_capture_counts_as_one_pawn_capture(
    game,
    expected_has_pawn_capture,
    expected_pawn_tries,
):
    game = _build_promotion_capture_game(game)
    promotion_captures = _promotion_capture_moves()

    assert promotion_captures <= set(game.possible_to_ask)
    assert game._count_legal_pawn_captures() == 1
    assert game._has_any_pawn_captures() is True
    assert game.current_turn_has_pawn_capture is expected_has_pawn_capture
    assert game.current_turn_pawn_tries == expected_pawn_tries


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected"),
    [
        pytest.param(
            BerkeleyGame(),
            KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.A5),
            id="berkeley-any",
        ),
        pytest.param(
            BerkeleyGame(any_rule=False),
            KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.A5),
            id="berkeley",
        ),
        pytest.param(
            CincinnatiGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.A5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_has_pawn_capture=False,
            ),
            id="cincinnati",
        ),
        pytest.param(
            Wild16Game(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.A5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_pawn_tries=0,
            ),
            id="wild16",
        ),
    ],
)
def test_rules_comparison_non_pawn_capture_is_still_legal_before_any_constraint(game, expected):
    game = _build_rules_comparison_game(game)

    assert game.ask_for(_piece_capture_move()) == expected


@pytest.mark.rules
def test_rules_comparison_berkeley_any_has_any_forces_a_pawn_capture():
    game = _build_rules_comparison_game(BerkeleyGame())

    assert game.ask_for(KSMove(QA.ASK_ANY)) == KSAnswer(MA.HAS_ANY)
    assert game.must_use_pawns is True
    assert game.ask_for(_piece_capture_move()) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)
    assert game.ask_for(_left_pawn_capture_move()) == KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.D5)


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
    ],
)
def test_rules_comparison_berkeley_family_can_try_pawn_captures_without_announcement(game):
    game = _build_rules_comparison_game(game)

    assert _left_pawn_capture_move() in game.possible_to_ask
    assert _right_pawn_capture_move() in game.possible_to_ask


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected"),
    [
        pytest.param(
            CincinnatiGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_has_pawn_capture=False,
            ),
            id="cincinnati",
        ),
        pytest.param(
            Wild16Game(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_pawn_tries=0,
            ),
            id="wild16",
        ),
    ],
)
def test_rules_comparison_automatic_pawn_capture_announcement_allows_pawn_tries(game, expected):
    game = _build_rules_comparison_game(game)

    assert _left_pawn_capture_move() in game.possible_to_ask
    assert _right_pawn_capture_move() in game.possible_to_ask
    assert game.ask_for(_left_pawn_capture_move()) == expected
