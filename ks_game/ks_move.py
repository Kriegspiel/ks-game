# -*- coding: utf-8 -*-

import enum

import chess


@enum.unique
class QuestionAnnouncement(enum.Enum):
    COMMON = 1
    ASK_ANY = 2


class KriegspielMove(object):
    '''docstring for KriegdpielMove'''
    def __init__(self, question_type, chess_move=None):
        super(KriegspielMove, self).__init__()
        # Validation
        if not isinstance(question_type, QuestionAnnouncement):
            raise TypeError
        if (question_type == QuestionAnnouncement.COMMON and
                not isinstance(chess_move, chess.Move)):
            raise TypeError
        self.question_type = question_type
        self.chess_move = chess_move

    def __str__(self):
        return '<KriegspielMove: {QA}, uci={chess_move}>'.format(
            QA=self.question_type,
            chess_move=self.chess_move
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, KriegspielMove):
            return False
        if (self.chess_move == other.chess_move and
                self.question_type == other.question_type):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.question_type.value < other.question_type.value:
            return True
        if self.question_type.value == other.question_type.value:
            if self.chess_move.uci() < other.chess_move.uci():
                return True
        return False

    def __hash__(self):
        return hash(self.__str__())


@enum.unique
class MainAnnouncement(enum.Enum):
    '''docstring for MoveAnnouncement'''
    IMPOSSIBLE_TO_ASK = 0  #enum.auto()
    ILLEGAL_MOVE = 1  #enum.auto()
    REGULAR_MOVE = 2  #enum.auto()
    CAPTURE_DONE = 3  #enum.auto()

    HAS_ANY = 4  #enum.auto()
    NO_ANY = 5  #enum.auto()


MOVE_DONE = [
    MainAnnouncement.REGULAR_MOVE,
    MainAnnouncement.CAPTURE_DONE
]


@enum.unique
class SpecialCaseAnnouncement(enum.Enum):
    '''docstring for SpecialCaseAnnouncement'''
    NONE = -1

    DRAW_TOOMANYREVERSIBLEMOVES = 1  #enum.auto()
    DRAW_STALEMATE = 2  #enum.auto()
    DRAW_INSUFFICIENT = 3  #enum.auto()

    CHECKMATE_WHITE_WINS = 4  #enum.auto()
    CHECKMATE_BLACK_WINS = 5  #enum.auto()

    CHECK_RANK = 6  #enum.auto()
    CHECK_FILE = 7  #enum.auto()
    CHECK_LONG_DIAGONAL = 8  #enum.auto()
    CHECK_SHORT_DIAGONAL = 9  #enum.auto()
    CHECK_KNIGHT = 10  #enum.auto()
    CHECK_DOUBLE = 11  #enum.auto()


class KriegspielAnswer(object):
    '''docstring for KriegdpielMove'''
    def __init__(self, main_announcement, **kwargs):
        super(KriegspielAnswer, self).__init__()
        # Validation
        if not isinstance(main_announcement, MainAnnouncement):
            raise TypeError

        self.main_announcement = main_announcement
        self.capture_at_square = None
        self.special_announcement = SpecialCaseAnnouncement.NONE
        self.move_done = False

        if main_announcement == MainAnnouncement.CAPTURE_DONE:
            if not isinstance(kwargs.get('capture_at_square'), int):
                raise TypeError
            self.capture_at_square = kwargs.get('capture_at_square')

        if 'special_announcement' in kwargs:
            if not isinstance(kwargs.get('special_announcement'), SpecialCaseAnnouncement):
                # if kwargs.get('special_announcement') is None:
                #     self.special_announcement = SpecialCaseAnnouncement.None
                # else:
                raise TypeError
            self.special_announcement = kwargs.get('special_announcement')

        if self.main_announcement in MOVE_DONE:
            self.move_done = True

    def __str__(self):
        capture_at = None
        if isinstance(self.capture_at_square, int):
            capture_at = chess.SQUARE_NAMES[self.capture_at_square]
        return '<KriegspielAnswer: {MA}, capture_at={CA}, special_case={SC}>'.format(
            MA=self.main_announcement,
            CA=capture_at,
            SC=self.special_announcement
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, KriegspielAnswer):
            return False
        if (self.main_announcement == other.main_announcement and
                self.capture_at_square == other.capture_at_square and
                self.special_announcement == other.special_announcement):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.main_announcement.value < other.main_announcement.value:
            return True
        if self.main_announcement.value == other.main_announcement.value:
            if self.capture_at_square < other.capture_at_square:
                return True
            if self.capture_at_square == other.capture_at_square:
                if self.special_announcement.value < other.special_announcement.value:
                    return True
        return False

    def __hash__(self):
        return hash(self.__str__())
