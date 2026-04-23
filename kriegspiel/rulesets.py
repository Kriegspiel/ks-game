"""Ruleset policies for Berkeley-family hidden-information chess."""

from __future__ import annotations

from dataclasses import dataclass

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import QuestionAnnouncement as QA


RULESET_BERKELEY = "berkeley"
RULESET_BERKELEY_ANY = "berkeley_any"


@dataclass(frozen=True)
class BerkeleyRulesetPolicy:
    """Policy layer for Berkeley-family rulesets.

    The hidden-board move engine is shared, while this policy decides
    which referee-only questions exist and how those questions constrain
    the next prompt. This keeps the current Berkeley behavior intact while
    making future Cincinnati / Wild 16 variants easier to add.
    """

    identifier: str
    allow_ask_any: bool

    def add_special_questions(self, possibilities: set[KSMove]) -> None:
        if self.allow_ask_any:
            possibilities.add(KSMove(QA.ASK_ANY))

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
        if answer.main_announcement == MA.HAS_ANY:
            pawn_captures = set(game._generate_possible_pawn_captures())
            game._set_possible_to_ask(game._possible_to_ask_set & pawn_captures)
        elif answer.main_announcement == MA.NO_ANY:
            pawn_captures = set(game._generate_possible_pawn_captures())
            game._set_possible_to_ask(game._possible_to_ask_set - pawn_captures)


def resolve_ruleset_policy(*, ruleset: str | None = None, any_rule: bool | None = None) -> BerkeleyRulesetPolicy:
    """Resolve legacy `any_rule` calls into an explicit ruleset policy."""
    if ruleset is None:
        allow_ask_any = True if any_rule is None else any_rule
        ruleset = RULESET_BERKELEY_ANY if allow_ask_any else RULESET_BERKELEY
    elif any_rule is not None:
        expected_any_rule = ruleset == RULESET_BERKELEY_ANY
        if expected_any_rule != any_rule:
            raise ValueError(
                f"ruleset {ruleset!r} conflicts with any_rule={any_rule!r}"
            )

    if ruleset == RULESET_BERKELEY_ANY:
        return BerkeleyRulesetPolicy(identifier=ruleset, allow_ask_any=True)
    if ruleset == RULESET_BERKELEY:
        return BerkeleyRulesetPolicy(identifier=ruleset, allow_ask_any=False)
    raise ValueError(f"Unsupported ruleset: {ruleset!r}")
