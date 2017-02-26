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
        return '<{QA}, uci={chess_move}>'.format(
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
