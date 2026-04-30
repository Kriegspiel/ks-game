"""Ruleset policies for hidden-information Kriegspiel variants."""

from __future__ import annotations

from dataclasses import dataclass

import chess
import chess.variant

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import CapturedPieceAnnouncement as CPA
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA


RULESET_BERKELEY = "berkeley"
RULESET_BERKELEY_ANY = "berkeley_any"
RULESET_CINCINNATI = "cincinnati"
RULESET_CRAZYKRIEG = "crazykrieg"
RULESET_ENGLISH = "english"
RULESET_RAND = "rand"
RULESET_WILD16 = "wild16"


@dataclass(frozen=True)
class BerkeleyRulesetPolicy:
    """Policy layer for shared Kriegspiel rulesets.

    The hidden-board move engine is shared, while this policy decides
    which referee-only questions exist and how those questions constrain
    the next prompt. This keeps the current Berkeley behavior intact while
    making ruleset variants easier to add without forking the engine.
    """

    identifier: str
    allow_ask_any: bool
    invalid_common_attempt_result: MA
    discard_illegal_attempts: bool
    public_illegal_attempts: bool
    typed_capture_announcements: bool
    announce_promotion: bool
    announce_next_turn_pawn_tries: bool
    announce_next_turn_has_pawn_capture: bool
    announce_next_turn_pawn_try_squares: bool
    release_ask_any_after_failed_pawn_try: bool
    stalemate_loses: bool
    board_type: type[chess.Board]
    exact_capture_announcements: bool
    announce_drops: bool

    def new_board(self):
        return self.board_type()

    def board_from_fen(self, fen: str):
        return self.board_type(fen)

    def add_special_questions(self, possibilities: set[KSMove]) -> None:
        if self.allow_ask_any:
            possibilities.add(KSMove(QA.ASK_ANY))

    def pawn_capture_attempts_for_prompt(self, game) -> set[KSMove]:
        """Return hidden pawn-capture tries that belong in this prompt."""
        pawn_captures = set(game._generate_possible_pawn_captures())
        if self.announce_next_turn_has_pawn_capture:
            return pawn_captures if game._has_any_pawn_captures() else set()
        if self.announce_next_turn_pawn_tries:
            return pawn_captures if game._count_legal_pawn_captures() > 0 else set()
        if self.announce_next_turn_pawn_try_squares:
            legal_sources = set(game._legal_pawn_capture_source_squares())
            return {
                move
                for move in pawn_captures
                if move.chess_move is not None and move.chess_move.from_square in legal_sources
            }
        return pawn_captures

    def classify_impossible_common_attempt(self, game=None) -> MA:
        if game is not None and game.must_use_pawns:
            return MA.IMPOSSIBLE_TO_ASK
        return self.invalid_common_attempt_result

    def handle_special_question(self, game, move: KSMove):
        if move.question_type != QA.ASK_ANY:
            return None
        if not self.allow_ask_any:
            return KSAnswer(MA.IMPOSSIBLE_TO_ASK)
        if game._has_any_pawn_captures():
            game._must_use_pawns = True
            return KSAnswer(MA.HAS_ANY)
        return KSAnswer(MA.NO_ANY)

    def apply_post_answer_constraints(self, game, answer: KSAnswer) -> None:
        if self.release_ask_any_after_failed_pawn_try and game.must_use_pawns and answer.main_announcement == MA.ILLEGAL_MOVE:
            game._must_use_pawns = False
            game._generate_possible_to_ask_list()
            return
        if not self.allow_ask_any:
            return
        if answer.main_announcement == MA.HAS_ANY:
            pawn_captures = set(game._generate_possible_pawn_captures())
            game._set_possible_to_ask(game._possible_to_ask_set & pawn_captures)
        elif answer.main_announcement == MA.NO_ANY:
            pawn_captures = set(game._generate_possible_pawn_captures())
            game._set_possible_to_ask(game._possible_to_ask_set - pawn_captures)

    def should_record_opponent_answer(self, move: KSMove, answer: KSAnswer) -> bool:
        if answer.main_announcement == MA.IMPOSSIBLE_TO_ASK:
            return False
        if answer.main_announcement == MA.ILLEGAL_MOVE and not self.public_illegal_attempts:
            return False
        return True

    def should_discard_attempt(self, move: KSMove, answer: KSAnswer) -> bool:
        if answer.main_announcement == MA.NO_ANY:
            return True
        if answer.main_announcement == MA.ILLEGAL_MOVE:
            return self.discard_illegal_attempts
        return False

    @staticmethod
    def _exact_piece_announcement_for(piece_type: int) -> CPA:
        exact_announcements = {
            chess.PAWN: CPA.PAWN,
            chess.KNIGHT: CPA.KNIGHT,
            chess.BISHOP: CPA.BISHOP,
            chess.ROOK: CPA.ROOK,
            chess.QUEEN: CPA.QUEEN,
        }
        return exact_announcements[piece_type]

    def captured_piece_announcement_for(
        self,
        captured_piece,
        *,
        board=None,
        captured_square=None,
    ) -> CPA | None:
        if not self.typed_capture_announcements or captured_piece is None:
            return None
        if self.exact_capture_announcements:
            if board is not None and captured_square is not None:
                promoted = getattr(board, "promoted", 0)
                if promoted & chess.BB_SQUARES[captured_square]:
                    return CPA.PAWN
            return self._exact_piece_announcement_for(captured_piece.piece_type)
        if captured_piece.piece_type == chess.PAWN:
            return CPA.PAWN
        return CPA.PIECE

    def dropped_piece_announcement_for(self, move: KSMove) -> CPA | None:
        if not self.announce_drops or move.chess_move is None or move.chess_move.drop is None:
            return None
        return self._exact_piece_announcement_for(move.chess_move.drop)

    def next_turn_pawn_tries(self, game) -> int | None:
        if not self.announce_next_turn_pawn_tries or game.game_over:
            return None
        return game._count_legal_pawn_captures()

    def next_turn_has_pawn_capture(self, game) -> bool | None:
        if not self.announce_next_turn_has_pawn_capture or game.game_over:
            return None
        return game._has_any_pawn_captures()

    def next_turn_pawn_try_squares(self, game) -> tuple[int, ...] | None:
        if not self.announce_next_turn_pawn_try_squares or game.game_over:
            return None
        return game._legal_pawn_capture_source_squares()


def resolve_ruleset_policy(*, ruleset: str | None = None, any_rule: bool | None = None) -> BerkeleyRulesetPolicy:
    """Resolve legacy `any_rule` calls into an explicit ruleset policy."""
    if ruleset is None:
        allow_ask_any = True if any_rule is None else any_rule
        ruleset = RULESET_BERKELEY_ANY if allow_ask_any else RULESET_BERKELEY
    elif any_rule is not None:
        expected_any_rule = ruleset in {RULESET_BERKELEY_ANY, RULESET_CRAZYKRIEG, RULESET_ENGLISH}
        if expected_any_rule != any_rule:
            raise ValueError(
                f"ruleset {ruleset!r} conflicts with any_rule={any_rule!r}"
            )

    if ruleset == RULESET_BERKELEY_ANY:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=True,
            invalid_common_attempt_result=MA.IMPOSSIBLE_TO_ASK,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=False,
            announce_promotion=False,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=False,
            stalemate_loses=False,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    if ruleset == RULESET_BERKELEY:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=False,
            invalid_common_attempt_result=MA.IMPOSSIBLE_TO_ASK,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=False,
            announce_promotion=False,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=False,
            stalemate_loses=False,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    if ruleset == RULESET_CINCINNATI:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=False,
            invalid_common_attempt_result=MA.NONSENSE,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=True,
            announce_promotion=False,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=True,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=False,
            stalemate_loses=False,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    if ruleset == RULESET_CRAZYKRIEG:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=True,
            invalid_common_attempt_result=MA.NONSENSE,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=True,
            announce_promotion=False,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=True,
            stalemate_loses=False,
            board_type=chess.variant.CrazyhouseBoard,
            exact_capture_announcements=True,
            announce_drops=True,
        )
    if ruleset == RULESET_ENGLISH:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=True,
            invalid_common_attempt_result=MA.ILLEGAL_MOVE,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=False,
            announce_promotion=False,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=True,
            stalemate_loses=False,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    if ruleset == RULESET_RAND:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=False,
            invalid_common_attempt_result=MA.NONSENSE,
            discard_illegal_attempts=True,
            public_illegal_attempts=True,
            typed_capture_announcements=True,
            announce_promotion=True,
            announce_next_turn_pawn_tries=False,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=True,
            release_ask_any_after_failed_pawn_try=False,
            stalemate_loses=True,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    if ruleset == RULESET_WILD16:
        return BerkeleyRulesetPolicy(
            identifier=ruleset,
            allow_ask_any=False,
            invalid_common_attempt_result=MA.ILLEGAL_MOVE,
            discard_illegal_attempts=True,
            public_illegal_attempts=False,
            typed_capture_announcements=True,
            announce_promotion=False,
            announce_next_turn_pawn_tries=True,
            announce_next_turn_has_pawn_capture=False,
            announce_next_turn_pawn_try_squares=False,
            release_ask_any_after_failed_pawn_try=False,
            stalemate_loses=False,
            board_type=chess.Board,
            exact_capture_announcements=False,
            announce_drops=False,
        )
    raise ValueError(f"Unsupported ruleset: {ruleset!r}")
