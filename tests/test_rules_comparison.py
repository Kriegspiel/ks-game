# -*- coding: utf-8 -*-

"""Tests that mirror the public rules-comparison table."""

import pytest

from kriegspiel.berkeley import BerkeleyGame, chess
from kriegspiel.cincinnati import CincinnatiGame
from kriegspiel.crazykrieg import CrazyKriegGame
from kriegspiel.english import EnglishGame
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.move import SpecialCaseAnnouncement as SCA
from kriegspiel.rand import RandGame
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


def _build_ask_any_release_game(game):
    game._board.clear()
    if hasattr(game._board, "pockets"):
        game._board.pockets[chess.WHITE].reset()
        game._board.pockets[chess.BLACK].reset()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    game._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.A5, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._board.set_piece_at(chess.D5, chess.Piece(chess.BISHOP, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def _piece_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.A1, chess.A5))


def _left_pawn_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.E4, chess.D5))


def _right_pawn_capture_move():
    return KSMove(QA.COMMON, chess.Move(chess.E4, chess.F5))


def _empty_right_pawn_try_move():
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


EN_PASSANT_DIAGONAL_CHECK_CASES = [
    pytest.param(
        {
            "king": chess.C2,
            "pawn_from": chess.E4,
            "captured_pawn": chess.D4,
            "ep_square": chess.D3,
            "expected_check": SCA.CHECK_LONG_DIAGONAL,
        },
        id="long-diagonal",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "pawn_from": chess.C4,
            "captured_pawn": chess.B4,
            "ep_square": chess.B3,
            "expected_check": SCA.CHECK_SHORT_DIAGONAL,
        },
        id="short-diagonal",
    ),
]


def _build_en_passant_diagonal_check_game(game, case):
    game._board.clear()
    game._board.turn = chess.BLACK
    game._board.set_piece_at(case["king"], chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(case["pawn_from"], chess.Piece(chess.PAWN, chess.BLACK))
    game._board.set_piece_at(case["captured_pawn"], chess.Piece(chess.PAWN, chess.WHITE))
    game._board.ep_square = case["ep_square"]
    game._generate_possible_to_ask_list()
    return game


DOUBLE_CHECK_CASES = [
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.F2,
            "blocker_from": chess.E2,
            "blocker_piece": chess.KNIGHT,
            "move": chess.Move(chess.E2, chess.D4),
            "expected_checks": {SCA.CHECK_RANK, SCA.CHECK_KNIGHT},
        },
        id="rank-knight",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.C5,
            "blocker_from": chess.C4,
            "blocker_piece": chess.KNIGHT,
            "move": chess.Move(chess.C4, chess.A3),
            "expected_checks": {SCA.CHECK_FILE, SCA.CHECK_KNIGHT},
        },
        id="file-knight",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.F2,
            "blocker_from": chess.E2,
            "blocker_piece": chess.BISHOP,
            "move": chess.Move(chess.E2, chess.D3),
            "expected_checks": {SCA.CHECK_RANK, SCA.CHECK_LONG_DIAGONAL},
        },
        id="rank-long-diagonal",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.F2,
            "blocker_from": chess.E2,
            "blocker_piece": chess.BISHOP,
            "move": chess.Move(chess.E2, chess.D1),
            "expected_checks": {SCA.CHECK_RANK, SCA.CHECK_SHORT_DIAGONAL},
        },
        id="rank-short-diagonal",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.C5,
            "blocker_from": chess.C4,
            "blocker_piece": chess.BISHOP,
            "move": chess.Move(chess.C4, chess.D3),
            "expected_checks": {SCA.CHECK_FILE, SCA.CHECK_LONG_DIAGONAL},
        },
        id="file-long-diagonal",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.C5,
            "blocker_from": chess.C4,
            "blocker_piece": chess.BISHOP,
            "move": chess.Move(chess.C4, chess.B3),
            "expected_checks": {SCA.CHECK_FILE, SCA.CHECK_SHORT_DIAGONAL},
        },
        id="file-short-diagonal",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.E4,
            "blocker_from": chess.D3,
            "blocker_piece": chess.KNIGHT,
            "move": chess.Move(chess.D3, chess.B4),
            "expected_checks": {SCA.CHECK_LONG_DIAGONAL, SCA.CHECK_KNIGHT},
        },
        id="long-diagonal-knight",
    ),
    pytest.param(
        {
            "king": chess.C2,
            "line_attacker": chess.A4,
            "blocker_from": chess.B3,
            "blocker_piece": chess.KNIGHT,
            "move": chess.Move(chess.B3, chess.D4),
            "expected_checks": {SCA.CHECK_SHORT_DIAGONAL, SCA.CHECK_KNIGHT},
        },
        id="short-diagonal-knight",
    ),
]


def _build_double_check_game(game, case):
    game._board.clear()
    game._board.turn = chess.BLACK
    game._board.set_piece_at(case["king"], chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(case["line_attacker"], chess.Piece(chess.QUEEN, chess.BLACK))
    game._board.set_piece_at(case["blocker_from"], chess.Piece(case["blocker_piece"], chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


@pytest.mark.rules
def test_rules_comparison_position_announces_ruleset_specific_pawn_capture_metadata():
    berkeley_any = _build_rules_comparison_game(BerkeleyGame())
    berkeley = _build_rules_comparison_game(BerkeleyGame(any_rule=False))
    cincinnati = _build_rules_comparison_game(CincinnatiGame())
    crazykrieg = _build_rules_comparison_game(CrazyKriegGame())
    english = _build_rules_comparison_game(EnglishGame())
    rand = _build_rules_comparison_game(RandGame())
    wild16 = _build_rules_comparison_game(Wild16Game())

    assert KSMove(QA.ASK_ANY) in berkeley_any.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in berkeley.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in cincinnati.possible_to_ask
    assert KSMove(QA.ASK_ANY) in crazykrieg.possible_to_ask
    assert KSMove(QA.ASK_ANY) in english.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in rand.possible_to_ask
    assert KSMove(QA.ASK_ANY) not in wild16.possible_to_ask

    assert berkeley_any.current_turn_has_pawn_capture is None
    assert berkeley_any.current_turn_pawn_tries is None
    assert berkeley.current_turn_has_pawn_capture is None
    assert berkeley.current_turn_pawn_tries is None
    assert cincinnati.current_turn_has_pawn_capture is True
    assert cincinnati.current_turn_pawn_tries is None
    assert crazykrieg.current_turn_has_pawn_capture is None
    assert crazykrieg.current_turn_pawn_tries is None
    assert crazykrieg.current_turn_pawn_try_squares is None
    assert english.current_turn_has_pawn_capture is None
    assert english.current_turn_pawn_tries is None
    assert english.current_turn_pawn_try_squares is None
    assert rand.current_turn_has_pawn_capture is None
    assert rand.current_turn_pawn_tries is None
    assert rand.current_turn_pawn_try_squares == (chess.E4,)
    assert wild16.current_turn_has_pawn_capture is None
    assert wild16.current_turn_pawn_tries == 2


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected_has_pawn_capture", "expected_pawn_tries"),
    [
        pytest.param(BerkeleyGame(), None, None, id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), None, None, id="berkeley"),
        pytest.param(CincinnatiGame(), True, None, id="cincinnati"),
        pytest.param(CrazyKriegGame(), None, None, id="crazykrieg"),
        pytest.param(EnglishGame(), None, None, id="english"),
        pytest.param(RandGame(), None, None, id="rand"),
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
    if isinstance(game, RandGame):
        assert game.current_turn_pawn_try_squares == (chess.D2,)


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected_promotion_announced"),
    [
        pytest.param(BerkeleyGame(), False, id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), False, id="berkeley"),
        pytest.param(CincinnatiGame(), False, id="cincinnati"),
        pytest.param(CrazyKriegGame(), False, id="crazykrieg"),
        pytest.param(EnglishGame(), False, id="english"),
        pytest.param(RandGame(), True, id="rand"),
        pytest.param(Wild16Game(), False, id="wild16"),
    ],
)
def test_rules_comparison_only_rand_announces_promotion(game, expected_promotion_announced):
    game = _build_promotion_capture_game(game)
    promotion_capture = KSMove(QA.COMMON, chess.Move(chess.D2, chess.C1, promotion=chess.QUEEN))

    answer = game.ask_for(promotion_capture)

    assert answer.main_announcement == MA.CAPTURE_DONE
    assert answer.promotion_announced is expected_promotion_announced


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
        pytest.param(CincinnatiGame(), id="cincinnati"),
        pytest.param(CrazyKriegGame(), id="crazykrieg"),
        pytest.param(EnglishGame(), id="english"),
        pytest.param(RandGame(), id="rand"),
        pytest.param(Wild16Game(), id="wild16"),
    ],
)
@pytest.mark.parametrize("case", EN_PASSANT_DIAGONAL_CHECK_CASES)
def test_rules_comparison_en_passant_capture_can_announce_diagonal_check(game, case):
    game = _build_en_passant_diagonal_check_game(game, case)
    move = chess.Move(case["pawn_from"], case["ep_square"])
    ks_move = KSMove(QA.COMMON, move)

    assert game._board.is_en_passant(move)
    assert ks_move in game.possible_to_ask
    answer = game.ask_for(ks_move)

    expected_piece = (
        CPA.PAWN
        if game.ruleset_id in {"cincinnati", "crazykrieg", "rand", "wild16"}
        else None
    )
    expected_capture_square = case["ep_square"] if game.ruleset_id == "english" else case["captured_pawn"]
    assert answer.main_announcement == MA.CAPTURE_DONE
    assert answer.capture_at_square == expected_capture_square
    assert answer.captured_piece_announcement == expected_piece
    assert answer.en_passant_announced is (game.ruleset_id == "english")
    assert answer.special_announcement == case["expected_check"]
    assert game._board.piece_at(case["captured_pawn"]) is None
    assert game._board.piece_at(case["ep_square"]) == chess.Piece(chess.PAWN, chess.BLACK)


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
        pytest.param(CincinnatiGame(), id="cincinnati"),
        pytest.param(CrazyKriegGame(), id="crazykrieg"),
        pytest.param(EnglishGame(), id="english"),
        pytest.param(RandGame(), id="rand"),
        pytest.param(Wild16Game(), id="wild16"),
    ],
)
@pytest.mark.parametrize("case", DOUBLE_CHECK_CASES)
def test_rules_comparison_double_check_preserves_component_announcements(game, case):
    game = _build_double_check_game(game, case)
    move = KSMove(QA.COMMON, case["move"])

    assert move in game.possible_to_ask
    answer = game.ask_for(move)

    assert answer.main_announcement == MA.REGULAR_MOVE
    assert answer.special_announcement == SCA.CHECK_DOUBLE
    assert {answer.check_1, answer.check_2} == case["expected_checks"]


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
            EnglishGame(),
            KSAnswer(MA.CAPTURE_DONE, capture_at_square=chess.A5),
            id="english",
        ),
        pytest.param(
            CrazyKriegGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.A5,
                captured_piece_announcement=CPA.KNIGHT,
            ),
            id="crazykrieg",
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
            RandGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.A5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_pawn_try_squares=tuple(),
            ),
            id="rand",
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
        pytest.param(CrazyKriegGame(), id="crazykrieg"),
        pytest.param(EnglishGame(), id="english"),
    ],
)
def test_rules_comparison_ask_any_can_be_asked_only_once_per_ply_after_no(game):
    ask_any = KSMove(QA.ASK_ANY)

    assert game.ask_for(ask_any) == KSAnswer(MA.NO_ANY)
    assert ask_any not in game.possible_to_ask
    assert game.ask_for(ask_any) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(CrazyKriegGame(), id="crazykrieg"),
        pytest.param(EnglishGame(), id="english"),
    ],
)
def test_rules_comparison_ask_any_can_be_asked_only_once_per_ply_after_yes(game):
    game = _build_rules_comparison_game(game)
    ask_any = KSMove(QA.ASK_ANY)

    assert game.ask_for(ask_any) == KSAnswer(MA.HAS_ANY)
    assert ask_any not in game.possible_to_ask
    assert game.ask_for(ask_any) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


@pytest.mark.rules
@pytest.mark.parametrize(
    ("game", "expected_impossible_common_attempt"),
    [
        pytest.param(CrazyKriegGame(), MA.NONSENSE, id="crazykrieg"),
        pytest.param(EnglishGame(), MA.ILLEGAL_MOVE, id="english"),
    ],
)
def test_rules_comparison_english_style_release_keeps_ask_any_single_use_per_ply(
    game,
    expected_impossible_common_attempt,
):
    game = _build_ask_any_release_game(game)
    ask_any = KSMove(QA.ASK_ANY)
    impossible_regular_attempt = KSMove(QA.COMMON, chess.Move(chess.G1, chess.G3))

    assert game.ask_for(ask_any) == KSAnswer(MA.HAS_ANY)
    assert game.ask_for(_empty_right_pawn_try_move()) == KSAnswer(MA.ILLEGAL_MOVE)
    assert game.must_use_pawns is False
    assert ask_any not in game.possible_to_ask

    assert game.ask_for(impossible_regular_attempt) == KSAnswer(expected_impossible_common_attempt)
    assert ask_any not in game.possible_to_ask
    assert game.ask_for(ask_any) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
        pytest.param(CincinnatiGame(), id="cincinnati"),
        pytest.param(RandGame(), id="rand"),
        pytest.param(Wild16Game(), id="wild16"),
    ],
)
def test_rules_comparison_rulesets_without_ask_any_reject_it_for_the_whole_ply(game):
    ask_any = KSMove(QA.ASK_ANY)

    assert ask_any not in game.possible_to_ask
    assert game.ask_for(ask_any) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)
    assert ask_any not in game.possible_to_ask
    assert game.ask_for(ask_any) == KSAnswer(MA.IMPOSSIBLE_TO_ASK)


@pytest.mark.rules
@pytest.mark.parametrize(
    "game",
    [
        pytest.param(BerkeleyGame(), id="berkeley-any"),
        pytest.param(BerkeleyGame(any_rule=False), id="berkeley"),
        pytest.param(CrazyKriegGame(), id="crazykrieg"),
        pytest.param(EnglishGame(), id="english"),
    ],
)
def test_rules_comparison_ask_any_rulesets_can_try_pawn_captures_without_announcement(game):
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
        pytest.param(
            RandGame(),
            KSAnswer(
                MA.CAPTURE_DONE,
                capture_at_square=chess.D5,
                captured_piece_announcement=CPA.PIECE,
                next_turn_pawn_try_squares=tuple(),
            ),
            id="rand",
        ),
    ],
)
def test_rules_comparison_automatic_pawn_capture_announcement_allows_pawn_tries(game, expected):
    game = _build_rules_comparison_game(game)

    assert _left_pawn_capture_move() in game.possible_to_ask
    assert _right_pawn_capture_move() in game.possible_to_ask
    assert game.ask_for(_left_pawn_capture_move()) == expected
