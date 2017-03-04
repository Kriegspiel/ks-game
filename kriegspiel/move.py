# -*- coding: utf-8 -*-

import enum

import chess


@enum.unique
class QuestionAnnouncement(enum.Enum):
    NONE = 0
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
        return '<KriegspielMove: {QA}, move={chess_move}>'.format(
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
        return self.__str__() < other.__str__()

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


SINGLE_CHECK = [
    SpecialCaseAnnouncement.CHECK_RANK,
    SpecialCaseAnnouncement.CHECK_FILE,
    SpecialCaseAnnouncement.CHECK_LONG_DIAGONAL,
    SpecialCaseAnnouncement.CHECK_SHORT_DIAGONAL,
    SpecialCaseAnnouncement.CHECK_KNIGHT
]


class KriegspielAnswer(object):
    '''docstring for KriegdpielMove'''
    def __init__(self, main_announcement, **kwargs):
        super(KriegspielAnswer, self).__init__()
        # Validation
        if not isinstance(main_announcement, MainAnnouncement):
            raise TypeError

        self._main_announcement = main_announcement
        self._capture_at_square = None
        self._special_announcement = SpecialCaseAnnouncement.NONE
        self._move_done = False
        self._check_1 = None
        self._check_2 = None

        if main_announcement == MainAnnouncement.CAPTURE_DONE:
            if not isinstance(kwargs.get('capture_at_square'), int):
                raise TypeError
            self._capture_at_square = kwargs['capture_at_square']

        if 'special_announcement' in kwargs:
            sca = kwargs['special_announcement']
            if isinstance(sca, SpecialCaseAnnouncement):
                self._special_announcement = sca
            elif isinstance(sca, tuple):
                if sca[0] == SpecialCaseAnnouncement.CHECK_DOUBLE:
                    self._special_announcement = SpecialCaseAnnouncement.CHECK_DOUBLE
                    for check in sca[1]:
                        if not check in SINGLE_CHECK:
                            raise TypeError
                    self._check_1 = sca[1][0]
                    self._check_2 = sca[1][1]
                else:
                    raise TypeError
            else:
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

        main_data = [
            'capture_at={CA}'.format(CA=capture_at),
            'special_case={SC}'.format(SC=self._special_announcement)
        ]

        if self._check_1 is not None or self._check_2 is not None:
            extra_data = 'check_1={c1}, check_2={c2}'.format(
                c1=self._check_1,
                c2=self._check_2
            )
            main_data.append(extra_data)

        return '<KriegspielAnswer: {MA}, {data}>'.format(
            MA=self._main_announcement,
            data=', '.join(main_data)
        )

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
