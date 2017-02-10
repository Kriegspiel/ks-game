# -*- coding: utf-8 -*-

import chess


ILLEGAL_MOVE = 'illegal'
REGULAR_MOVE = 'regular move done'
CAPUTRE_DONE = 'capture'

HAS_ANY = 'has any'
NO_ANY = 'no any'
ASK_ANY = 'any?'

CHECKMATE = 'checkmate'
STALEMATE = 'stalemate'
FIVEFOLD_REPETITION = 'fivefold repetition'
SEVENTYFIVE_MOVES = 'seventyfive moves'
CHECK = 'check'


class BerkeleyGame(object):
    '''docstring for BerkeleyGame'''

    def __init__(self):
        super(BerkeleyGame).__init__()
        self.board = chess.Board()
        self._must_use_pawns = False
    
    def ask_for(self, move):
        if isinstance(move, chess.Move):
            if self._if_legal_move(move):
                if not self._check_if_must_use_pawns_rule(move):
                    return ILLEGAL_MOVE, None, None
                captured_square = self._make_move(move)
                special_case = self._check_special_cases()
                if captured_square is not None:
                    # Cpature done
                    return CAPUTRE_DONE, captured_square, special_case
                # Regular move done
                return REGULAR_MOVE, None, special_case
            # No move done
            return ILLEGAL_MOVE, None, None
        elif isinstance(move, str):
            # Any rule
            if move == ASK_ANY:
                if self._if_any_pawn_captures():
                    self._must_use_pawns = True
                    return HAS_ANY, None, None
                else:
                    return NO_ANY, None, None
            else:
                raise KeyError
        else:
            raise TypeError

    def _check_if_must_use_pawns_rule(self, move):
        if self._must_use_pawns:
            return self.board.piece_type_at(move.from_square) == chess.PAWN
        return True

    def _check_special_cases(self):
        if self.board.is_game_over():
            return CHECKMATE
        if self.board.is_stalemate():
            return STALEMATE
        if self.board.is_fivefold_repetition():
            return FIVEFOLD_REPETITION
        if self.board.is_seventyfive_moves():
            return SEVENTYFIVE_MOVES
        if self.board.is_check():
            return CHECK
        return None

    def _make_move(self, move):
        def get_captured_square(move):
            if not self.board.is_en_passant(move):
                return move.to_square
            else:
                if self.board.turn == chess.WHITE:
                    return move.to_square - 8
                else:
                    return move.to_square + 8

        self._must_use_pawns = False
        if self.board.is_capture(move):
            captured_square = get_captured_square(move)
            self.board.push(move)
            return captured_square
        else:
            self.board.push(move)
            return None

    def _if_any_pawn_captures(self):
        pawn_squares = self.board.pieces(chess.PAWN, self.board.turn)
        for move in self.board.legal_moves:
            if move.from_square in pawn_squares:
                if self.board.is_capture(move):
                    return True
        return False

    def _if_legal_move(self, move):
        return move in self.board.legal_moves
