"""Public snapshot types for Kriegspiel engine state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import chess

from kriegspiel.move import KriegspielAnswer
from kriegspiel.move import KriegspielMove
from kriegspiel.move import QuestionAnnouncement


MoveTurn = Tuple[Tuple[KriegspielMove, KriegspielAnswer], ...]
OpponentTurn = Tuple[Tuple[QuestionAnnouncement, KriegspielAnswer], ...]


@dataclass(frozen=True)
class ScoresheetSnapshot:
    """Serializable, public view of a player's scoresheet state."""

    color: chess.Color
    moves_own: Tuple[MoveTurn, ...]
    moves_opponent: Tuple[OpponentTurn, ...]
    last_move_number: int


@dataclass(frozen=True)
class MaterialSideSummary:
    """Public material status for one color."""

    pieces_remaining: int
    pawns_captured: Optional[int] = None


@dataclass(frozen=True)
class PublicMaterialSummary:
    """Public material status derived from referee announcements."""

    white: MaterialSideSummary
    black: MaterialSideSummary


@dataclass(frozen=True)
class KriegspielGameSnapshot:
    """Serializable, public view of a hidden-board Kriegspiel game."""

    ruleset_id: str
    any_rule: bool
    board_fen: str
    move_stack: Tuple[str, ...]
    must_use_pawns: bool
    game_over: bool
    possible_to_ask: Optional[Tuple[KriegspielMove, ...]]
    white_scoresheet: ScoresheetSnapshot
    black_scoresheet: ScoresheetSnapshot


# Backward-compatible alias for older Berkeley-named APIs.
BerkeleyGameSnapshot = KriegspielGameSnapshot


def completed_moves_from_turn(turn: MoveTurn) -> Tuple[str, ...]:
    """Return UCI moves for successful COMMON questions within a single turn."""
    completed_moves = []
    for move, answer in turn:
        if move.question_type != QuestionAnnouncement.COMMON or not answer.move_done:
            continue
        if move.chess_move is None:
            raise ValueError("Scoresheet move is missing chess_move")
        completed_moves.append(move.chess_move.uci())

    if len(completed_moves) > 1:
        raise ValueError("Scoresheet turn contains multiple completed moves")

    return tuple(completed_moves)


def move_stack_from_scoresheets(
    white_scoresheet: ScoresheetSnapshot, black_scoresheet: ScoresheetSnapshot
) -> Tuple[str, ...]:
    """Extract the executed chess moves recorded in both players' own scoresheets."""
    extracted = []
    max_turns = max(len(white_scoresheet.moves_own), len(black_scoresheet.moves_own))

    for turn_index in range(max_turns):
        if turn_index < len(white_scoresheet.moves_own):
            extracted.extend(completed_moves_from_turn(white_scoresheet.moves_own[turn_index]))
        if turn_index < len(black_scoresheet.moves_own):
            extracted.extend(completed_moves_from_turn(black_scoresheet.moves_own[turn_index]))

    return tuple(extracted)
