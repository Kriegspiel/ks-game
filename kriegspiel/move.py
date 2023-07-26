# -*- coding: utf-8 -*-

import enum

import chess


@enum.unique
class QuestionAnnouncement(enum.Enum):
    """
    There are two main question types (Question Announcements)
    in a typical Kriegspiel game, plus a technical NONE option:
    1. Common question, when a player asks for a chess move.
    2. ASK_NY — special question type, when a player asks if there
        are any valid captures by pawns. This question is not valid
        in all Kriegspiel variants, but very common and makes the
        game much more dynamic.
    """

    NONE = 0
    COMMON = 1
    ASK_ANY = 2


class KriegspielMove(object):
    """
    Basic class to define main operations and validations
    for general Kriegspiel move.
    """

    def __init__(self, question_type, chess_move=None):
        super(KriegspielMove, self).__init__()
        # Validation, that question type is from valid enum
        if not isinstance(question_type, QuestionAnnouncement):
            raise TypeError
        # Validation, that if the question is from common type,
        # then it should be valid chess move object
        if question_type == QuestionAnnouncement.COMMON and not isinstance(chess_move, chess.Move):
            raise TypeError
        self.question_type = question_type
        self.chess_move = chess_move

    def __str__(self):
        return f"<KriegspielMove: {self.question_type}, move={self.chess_move}>"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, KriegspielMove):
            return False
        if self.chess_move == other.chess_move and self.question_type == other.question_type:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.__str__() < other.__str__()

    def __hash__(self):
        return hash(self.__str__())


@enum.unique
class MainAnnouncement(enum.Enum):
    """
    There are 6 valid options for how to respond to Question Announcement
    in the Kriegspiel game.

    Four of them are for the Common Question type:
    1. IMPOSSIBLE_TO_ASK — such a move is illegal from regular chess
        perspective and that should be known by the player who asks.
        In general, players should not ask such kind of questions, and
        it should not be considered as a question announcement at all.
    2. ILLEGAL_MOVE — a move is illegal from a regular chess perspective,
        but it is unknown to the player who asks. That is new information
        for the players.
    3. REGULAR_MOVE — a move is valid and immediately done. No capture happened.
    4. REGULAR_MOVE — a move is valid and immediately done. Capture happened.

    And there are two responses, that are special from ASK_ANY type of
    Question announcement:
    1. HAS_ANY — there is at least one valid capture available for the pawn
        of the player who asks. After that pawn capture should happen by
        asking for each possible capture, the order is not defined. A player
        must ask only for pawn capture Common Question after that.
    2. NO_ANY — there are no available pawn captures for the player, who
        asks. After that player can continue asking any Common Questions.
    """

    IMPOSSIBLE_TO_ASK = 0
    ILLEGAL_MOVE = 1
    REGULAR_MOVE = 2
    CAPTURE_DONE = 3

    HAS_ANY = 4
    NO_ANY = 5


# There are two types of Main Announcements that correspond to MOVE_DONE.
MOVE_DONE = [MainAnnouncement.REGULAR_MOVE, MainAnnouncement.CAPTURE_DONE]


@enum.unique
class SpecialCaseAnnouncement(enum.Enum):
    """
    If the move set the game in one of the special conditions,
    then Special Case Announcement is used. There are five of them
    for game end cases — as DRAW or CHECKMATE. Also, six of then for
    CHECK case. And one of them is technical — NONE.
    """

    NONE = -1

    DRAW_TOOMANYREVERSIBLEMOVES = 1
    DRAW_STALEMATE = 2
    DRAW_INSUFFICIENT = 3

    CHECKMATE_WHITE_WINS = 4
    CHECKMATE_BLACK_WINS = 5

    CHECK_RANK = 6
    CHECK_FILE = 7
    CHECK_LONG_DIAGONAL = 8
    CHECK_SHORT_DIAGONAL = 9
    CHECK_KNIGHT = 10
    CHECK_DOUBLE = 11


# Five options for Singe Check
SINGLE_CHECK = [
    SpecialCaseAnnouncement.CHECK_RANK,
    SpecialCaseAnnouncement.CHECK_FILE,
    SpecialCaseAnnouncement.CHECK_LONG_DIAGONAL,
    SpecialCaseAnnouncement.CHECK_SHORT_DIAGONAL,
    SpecialCaseAnnouncement.CHECK_KNIGHT,
]


class KriegspielAnswer(object):
    """
    Basic class to define main operations and validation for
    Kriegspiel answer.
    """

    def __init__(self, main_announcement, **kwargs):
        super(KriegspielAnswer, self).__init__()
        # Validation, that main announcement, can be only
        # Main Announcement.
        if not isinstance(main_announcement, MainAnnouncement):
            raise TypeError

        self._main_announcement = main_announcement
        self._capture_at_square = None
        self._special_announcement = SpecialCaseAnnouncement.NONE
        self._move_done = False
        self._check_1 = None
        self._check_2 = None

        if main_announcement == MainAnnouncement.CAPTURE_DONE:
            # Validation, that when capture is done, then valid square should
            # announced. Chess lib store squares as ints.
            # TODO: Check if the square number INT is in the valid range.
            if not isinstance(kwargs.get("capture_at_square"), int):
                raise TypeError
            self._capture_at_square = kwargs["capture_at_square"]

        if "special_announcement" in kwargs:
            sca = kwargs["special_announcement"]
            if isinstance(sca, SpecialCaseAnnouncement):
                self._special_announcement = sca
            elif isinstance(sca, tuple):
                if sca[0] == SpecialCaseAnnouncement.CHECK_DOUBLE:
                    self._special_announcement = SpecialCaseAnnouncement.CHECK_DOUBLE
                    # TODO: Check if there are exactly two checks when double check.
                    for check in sca[1]:
                        # Validation, that both checks correspond to double check
                        # are single check.
                        if not check in SINGLE_CHECK:
                            raise TypeError
                    self._check_1 = sca[1][0]
                    self._check_2 = sca[1][1]
                else:
                    # Validation, that if it's tuple, then only double check
                    # is the option.
                    raise TypeError
            else:
                # Validation, that Special Case Announcement could be SCA or tuple.
                raise TypeError

        if self._main_announcement in MOVE_DONE:
            self._move_done = True

    @property
    def main_announcement(self):
        return self._main_announcement

    @property
    def capture_at_square(self):
        return self._capture_at_square

    @property
    def special_announcement(self):
        return self._special_announcement

    @property
    def move_done(self):
        return self._move_done

    @property
    def check_1(self):
        return self._check_1

    @property
    def check_2(self):
        return self._check_2

    def __str__(self):
        capture_at = None
        if isinstance(self._capture_at_square, int):
            capture_at = chess.SQUARE_NAMES[self._capture_at_square]

        main_data = [f"capture_at={capture_at}", f"special_case={self._special_announcement}"]

        if self._check_1 is not None or self._check_2 is not None:
            extra_data = f"check_1={self._check_1}, check_2={self._check_2}"
            main_data.append(extra_data)

        return f'<KriegspielAnswer: {self._main_announcement}, {", ".join(main_data)}>'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.__str__() < other.__str__()

    def __hash__(self):
        return hash(self.__str__())


class KriegspielScoresheet:
    def __init__(self, color=chess.WHITE):
        self.__color = color
        self.__moves_own = []
        self.__moves_opponent = []
        self.__last_move_number = 0

    @property
    def moves_own(self):
        return self.__moves_own

    @property
    def moves_opponent(self):
        return self.__moves_opponent

    @property
    def color(self):
        return self.__color

    def was_the_last_move_ended(self, color):
        if self.__color == color:
            last_set_of_questions = self.__moves_own[-1]
        else:
            last_set_of_questions = self.__moves_opponent[-1]
        last_pair = last_set_of_questions[-1]
        last_answer = last_pair[1]
        return last_answer.move_done

    def __get_current_move_number(self):
        if self.__last_move_number == 0:
            self.__last_move_number += 1
            return self.__last_move_number
        # One of the list is smaller → we are still in progress.
        if len(self.__moves_own) < len(self.__moves_opponent) or len(self.__moves_opponent) < len(self.__moves_own):
            return self.__last_move_number
        # If the same lenghts of moves' lists.
        if self.was_the_last_move_ended(chess.WHITE) and self.was_the_last_move_ended(chess.BLACK):
            self.__last_move_number += 1
            return self.__last_move_number
        # Same lengths of moves' lists, but one of the lists (black one), is still in progress.
        return self.__last_move_number

    def record_move_own(self, move, answer):
        if not isinstance(move, KriegspielMove):
            raise ValueError
        if not isinstance(answer, KriegspielAnswer):
            raise ValueError
        current_move_number = self.__get_current_move_number()
        if current_move_number == len(self.__moves_own):
            self.__moves_own[-1].append((move, answer))
        else:
            self.__moves_own.append([(move, answer)])

    def record_move_opponent(self, question, answer):
        if not isinstance(question, QuestionAnnouncement):
            raise ValueError
        if not isinstance(answer, KriegspielAnswer):
            raise ValueError
        current_move_number = self.__get_current_move_number()
        if current_move_number == len(self.__moves_opponent):
            self.__moves_opponent[-1].append((question, answer))
        else:
            self.__moves_opponent.append([(question, answer)])
