# -*- coding: utf-8 -*-

"""Tests for the neutral shared-engine public API."""

import os
import tempfile

import chess
import pytest

from kriegspiel import BerkeleyGame
from kriegspiel import CincinnatiGame
from kriegspiel import CrazyKriegGame
from kriegspiel import EnglishGame
from kriegspiel import KriegspielGame
from kriegspiel import KriegspielMove as KSMove
from kriegspiel import MainAnnouncement as MA
from kriegspiel import MaterialSideSummary
from kriegspiel import PublicMaterialSummary
from kriegspiel import PublicReserveSummary
from kriegspiel import QuestionAnnouncement as QA
from kriegspiel import RandGame
from kriegspiel import ReserveSideSummary
from kriegspiel import Wild16Game
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.rulesets import RULESET_BERKELEY
from kriegspiel.rulesets import RULESET_BERKELEY_ANY
from kriegspiel.snapshot import KriegspielGameSnapshot
from kriegspiel.snapshot import ScoresheetSnapshot
from kriegspiel.snapshot import move_stack_from_scoresheets


def test_generic_game_defaults_to_berkeley_any():
    game = KriegspielGame()

    assert game.ruleset_id == RULESET_BERKELEY_ANY
    assert game.any_rule is True
    assert game.current_turn_has_pawn_capture is None
    assert game.current_turn_pawn_tries is None


def test_generic_game_from_snapshot_returns_generic_class():
    game = KriegspielGame(ruleset=RULESET_BERKELEY)
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))

    restored = KriegspielGame.from_snapshot(game.snapshot())

    assert isinstance(restored, KriegspielGame)
    assert restored.__class__ is KriegspielGame
    assert restored.ruleset_id == RULESET_BERKELEY
    assert restored._board.fen() == game._board.fen()


def test_generic_game_load_game_returns_generic_class():
    game = KriegspielGame(ruleset=RULESET_BERKELEY)
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        filename = handle.name

    try:
        game.save_game(filename)
        restored = KriegspielGame.load_game(filename)
    finally:
        os.unlink(filename)

    assert isinstance(restored, KriegspielGame)
    assert restored.__class__ is KriegspielGame
    assert restored._board.fen() == game._board.fen()


def test_generic_game_from_snapshot_rejects_wrong_type():
    with pytest.raises(TypeError, match="KriegspielGameSnapshot"):
        KriegspielGame.from_snapshot("not-a-snapshot")


def test_berkeley_name_remains_available():
    game = BerkeleyGame(any_rule=False)

    assert isinstance(game, BerkeleyGame)
    assert isinstance(game, KriegspielGame)
    assert game.ruleset_id == RULESET_BERKELEY


def test_berkeley_game_is_wrapper_subclass():
    assert issubclass(BerkeleyGame, KriegspielGame)
    assert not issubclass(KriegspielGame, BerkeleyGame)


def test_generic_snapshot_alias_is_exported():
    snapshot = KriegspielGame().snapshot()

    assert isinstance(snapshot, KriegspielGameSnapshot)


def test_move_stack_from_scoresheets_handles_black_only_turns():
    black_move = KSMove(QA.COMMON, chess.Move.from_uci("e7e5"))
    black_answer = KSAnswer(MA.REGULAR_MOVE)
    white_scoresheet = ScoresheetSnapshot(
        color=chess.WHITE,
        moves_own=tuple(),
        moves_opponent=tuple(),
        last_move_number=0,
    )
    black_scoresheet = ScoresheetSnapshot(
        color=chess.BLACK,
        moves_own=(((black_move, black_answer),),),
        moves_opponent=tuple(),
        last_move_number=1,
    )

    assert move_stack_from_scoresheets(white_scoresheet, black_scoresheet) == ("e7e5",)


@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
        pytest.param(EnglishGame(), id="english"),
    ],
)
def test_public_material_summary_hides_pawn_capture_counts_for_untyped_rulesets(game):
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5")))

    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=16, pawns_captured=None),
        black=MaterialSideSummary(pieces_remaining=15, pawns_captured=None),
    )


@pytest.mark.parametrize(
    ("game", "expected_answer"),
    [
        pytest.param(
            CincinnatiGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PAWN,
                next_turn_has_pawn_capture=False,
            ),
            id="cincinnati",
        ),
        pytest.param(
            Wild16Game(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PAWN,
                next_turn_pawn_tries=0,
            ),
            id="wild16",
        ),
        pytest.param(
            RandGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PAWN,
                next_turn_pawn_try_squares=tuple(),
            ),
            id="rand",
        ),
    ],
)
def test_public_material_summary_counts_public_pawn_captures_for_typed_rulesets(game, expected_answer):
    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
        black=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
    )

    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e2e4")))
    game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("d7d5")))

    assert game.ask_for(KSMove(QA.COMMON, chess.Move.from_uci("e4d5"))) == expected_answer
    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
        black=MaterialSideSummary(pieces_remaining=15, pawns_captured=1),
    )


@pytest.mark.parametrize(
    ("game", "expected_answer"),
    [
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
        pytest.param(
            RandGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.A5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_pawn_try_squares=tuple(),
            ),
            id="rand",
        ),
    ],
)
def test_public_material_summary_keeps_non_pawn_captures_out_of_pawn_count(game, expected_answer):
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A5, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))) == expected_answer
    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
        black=MaterialSideSummary(pieces_remaining=15, pawns_captured=0),
    )


def test_public_material_summary_does_not_treat_silent_promotion_as_a_pawn_capture():
    game = Wild16Game()
    game._board.clear()
    game._board.set_piece_at(chess.F3, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.BLACK))
    game._board.turn = chess.BLACK
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C1, promotion=chess.QUEEN))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.C1,
        captured_piece_announcement=CPA.PIECE,
        next_turn_pawn_tries=0,
    )
    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=15, pawns_captured=0),
        black=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
    )


def test_public_material_summary_handles_rand_announced_promotion_without_pawn_capture():
    game = RandGame()
    game._board.clear()
    game._board.set_piece_at(chess.F3, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.BLACK))
    game._board.turn = chess.BLACK
    game._generate_possible_to_ask_list()

    assert game.ask_for(KSMove(QA.COMMON, chess.Move(chess.D2, chess.C1, promotion=chess.QUEEN))) == KSAnswer(
        MA.CAPTURE_DONE,
        capture_at_square=chess.C1,
        captured_piece_announcement=CPA.PIECE,
        promotion_announced=True,
        next_turn_pawn_try_squares=tuple(),
    )
    assert game.public_material_summary == PublicMaterialSummary(
        white=MaterialSideSummary(pieces_remaining=15, pawns_captured=0),
        black=MaterialSideSummary(pieces_remaining=16, pawns_captured=0),
    )


def test_public_reserve_summary_is_zero_for_non_drop_rulesets():
    assert BerkeleyGame().public_reserve_summary == PublicReserveSummary(
        white=ReserveSideSummary(),
        black=ReserveSideSummary(),
    )


def test_package_root_exports_variant_entrypoints():
    assert KriegspielGame.__name__ == "KriegspielGame"
    assert BerkeleyGame.__name__ == "BerkeleyGame"
    assert CincinnatiGame.__name__ == "CincinnatiGame"
    assert CrazyKriegGame.__name__ == "CrazyKriegGame"
    assert EnglishGame.__name__ == "EnglishGame"
    assert RandGame.__name__ == "RandGame"
    assert Wild16Game.__name__ == "Wild16Game"
    assert MaterialSideSummary.__name__ == "MaterialSideSummary"
    assert PublicMaterialSummary.__name__ == "PublicMaterialSummary"
    assert PublicReserveSummary.__name__ == "PublicReserveSummary"
    assert ReserveSideSummary.__name__ == "ReserveSideSummary"
