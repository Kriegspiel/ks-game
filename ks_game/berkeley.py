# -*- coding: utf-8 -*-

import enum

import chess


@enum.unique
class MoveAnnouncement(enum.Enum):
    '''docstring for MoveAnnouncement'''
    ILLEGAL_MOVE = 1  #enum.auto()
    REGULAR_MOVE = 2  #enum.auto()
    CAPUTRE_DONE = 3  #enum.auto()


@enum.unique
class AnyRuleAnnouncement(enum.Enum):
    '''docstring for AnyRuleAnnouncement'''
    HAS_ANY = 1  #enum.auto()
    NO_ANY = 2  #enum.auto()
    ASK_ANY = 3  #enum.auto()


@enum.unique
class SpecialCaseAnnouncement(enum.Enum):
    '''docstring for SpecialCaseAnnouncement'''
    CHECKMATE = 1  #enum.auto()
    STALEMATE = 2  #enum.auto()
    FIVEFOLD_REPETITION = 3  #enum.auto()
    SEVENTYFIVE_MOVES = 4  #enum.auto()
    CHECK = 5  #enum.auto()


class BerkeleyGame(object):
    '''docstring for BerkeleyGame'''

    def __init__(self):
        super(BerkeleyGame).__init__()
        self.board = chess.Board()
        self._must_use_pawns = False
    
    def ask_for(self, move):
        '''
        return (MoveAnnouncement, captured_square, special_case)
        '''
        if isinstance(move, chess.Move):
            # Player asks about normal move
            if self._is_legal_move(move):
                # Move is legal in normal chess
                if not self._check_if_must_use_pawns_rule(move):
                    # Move is illigal, because player have asked
                    # about any possible pawn captures and there
                    # are some pawn captures, but now tries to
                    # play another piece.
                    return (
                        MoveAnnouncement.ILLEGAL_MOVE,
                        None,
                        None
                    )
                # Perform normal move
                captured_square = self._make_move(move)
                special_case = self._check_special_cases()
                if captured_square is not None:
                    # If it was capture
                    return (
                        MoveAnnouncement.CAPUTRE_DONE,
                        captured_square,
                        special_case
                    )
                # If it was regular move
                return (
                    MoveAnnouncement.REGULAR_MOVE,
                    None,
                    special_case
                )
            # If move is illegal
            return (
                MoveAnnouncement.ILLEGAL_MOVE,
                None,
                None
            )
        elif move == AnyRuleAnnouncement.ASK_ANY:
            # Any Rule. Asking for any available pawn captures.
            if self._has_any_pawn_captures():
                self._must_use_pawns = True
                return (
                    AnyRuleAnnouncement.HAS_ANY,
                    None,
                    None
                )
            else:
                return (
                    AnyRuleAnnouncement.NO_ANY,
                    None,
                    None
                )
        else:
            raise TypeError

    def _check_if_must_use_pawns_rule(self, move):
        if self._must_use_pawns:
            return self.board.piece_type_at(move.from_square) == chess.PAWN
        return True

    def _check_special_cases(self):
        if self.board.is_game_over():
            return SpecialCaseAnnouncement.CHECKMATE
        if self.board.is_stalemate():
            return SpecialCaseAnnouncement.STALEMATE
        if self.board.is_fivefold_repetition():
            return SpecialCaseAnnouncement.FIVEFOLD_REPETITION
        if self.board.is_seventyfive_moves():
            return SpecialCaseAnnouncement.SEVENTYFIVE_MOVES
        if self.board.is_check():
            return SpecialCaseAnnouncement.CHECK
        return None

    def _get_captured_square(self, move):
        if not self.board.is_en_passant(move):
            return move.to_square
        else:
            if self.board.turn == chess.WHITE:
                return move.to_square - 8
            else:
                return move.to_square + 8

    def _make_move(self, move):
        self._must_use_pawns = False
        if self.board.is_capture(move):
            captured_square = self._get_captured_square(move)
            self.board.push(move)
            return captured_square
        else:
            self.board.push(move)
            return None

    def _has_any_pawn_captures(self):
        pawn_squares = self.board.pieces(chess.PAWN, self.board.turn)
        for move in self.board.legal_moves:
            if move.from_square in pawn_squares:
                if self.board.is_capture(move):
                    return True
        return False

    def _is_legal_move(self, move):
        return move in self.board.legal_moves
