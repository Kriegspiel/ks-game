# -*- coding: utf-8 -*-

"""Focused policy tests for shared ruleset behavior."""

import chess

from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.rulesets import RULESET_BERKELEY
from kriegspiel.rulesets import RULESET_BERKELEY_ANY
from kriegspiel.rulesets import RULESET_WILD16
from kriegspiel.rulesets import resolve_ruleset_policy


def test_resolve_ruleset_policy_accepts_matching_any_rule_flags():
    assert resolve_ruleset_policy(ruleset=RULESET_BERKELEY_ANY, any_rule=True).identifier == RULESET_BERKELEY_ANY
    assert resolve_ruleset_policy(ruleset=RULESET_BERKELEY, any_rule=False).identifier == RULESET_BERKELEY


def test_ruleset_policy_controls_opponent_visibility():
    public_policy = resolve_ruleset_policy(ruleset=RULESET_BERKELEY_ANY)
    private_policy = resolve_ruleset_policy(ruleset=RULESET_WILD16)
    move = KSMove(QA.COMMON, chess.Move.from_uci("e2e4"))

    assert public_policy.should_record_opponent_answer(move, KSAnswer(MA.IMPOSSIBLE_TO_ASK)) is False
    assert public_policy.should_record_opponent_answer(move, KSAnswer(MA.ILLEGAL_MOVE)) is True
    assert private_policy.should_record_opponent_answer(move, KSAnswer(MA.ILLEGAL_MOVE)) is False
    assert private_policy.should_record_opponent_answer(move, KSAnswer(MA.REGULAR_MOVE)) is True


def test_ruleset_policy_announces_piece_captures_for_wild16():
    policy = resolve_ruleset_policy(ruleset=RULESET_WILD16)

    assert policy.captured_piece_announcement_for(None) is None
    assert policy.captured_piece_announcement_for(chess.Piece(chess.PAWN, chess.WHITE)) == CPA.PAWN
    assert policy.captured_piece_announcement_for(chess.Piece(chess.ROOK, chess.WHITE)) == CPA.PIECE
