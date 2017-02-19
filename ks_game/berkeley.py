# -*- coding: utf-8 -*-

import enum

import chess

from ks_game.ks_move import KriegspielMove as KSMove
from ks_game.ks_move import QuestionAnnouncement as QA


@enum.unique
class MoveAnnouncement(enum.Enum):
    '''docstring for MoveAnnouncement'''
    IMPOSSIBLE_TO_ASK = 0  #enum.auto()
    ILLEGAL_MOVE = 1  #enum.auto()
    REGULAR_MOVE = 2  #enum.auto()
    CAPTURE_DONE = 3  #enum.auto()

    HAS_ANY = 4  #enum.auto()
    NO_ANY = 5  #enum.auto()


@enum.unique
class SpecialCaseAnnouncement(enum.Enum):
    '''docstring for SpecialCaseAnnouncement'''
    DRAW_FIVEFOLD = 1  #enum.auto()
    DRAW_SEVENTYFIVE = 2  #enum.auto()
    DRAW_STALEMATE = 3  #enum.auto()
    DRAW_INSUFFICIENT = 4  #enum.auto()

    CHECKMATE_WHITE_WINS = 5  #enum.auto()
    CHECKMATE_BLACK_WINS = 6  #enum.auto()

    CHECK_RANK = 7  #enum.auto()
    CHECK_FILE = 8  #enum.auto()
    CHECK_LONG_DIAGONAL = 9  #enum.auto()
    CHECK_SHORT_DIAGONAL = 10  #enum.auto()
    CHECK_KNIGHT = 11  #enum.auto()
    CHECK_DOUBLE = 12  #enum.auto()


class BerkeleyGame(object):
    '''docstring for BerkeleyGame'''

    def __init__(self):
        super(BerkeleyGame).__init__()
        self.board = chess.Board()
        self._must_use_pawns = False
        self._generate_possible_to_ask_list()

    def ask_for(self, move):
        '''
        return (MoveAnnouncement, captured_square, SpecialCaseAnnouncement)
        '''
        if not isinstance(move, KSMove):
            raise TypeError

        if move not in self.possible_to_ask:
            return (
                MoveAnnouncement.IMPOSSIBLE_TO_ASK,
                None,
                None
            )

        if move.question_type == QA.COMMON:
            # Player asks about common move
            if self._is_legal_move(move.chess_move):
                # Move is legal in normal chess
                if not self._check_if_must_use_pawns_rule(move.chess_move):
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
                captured_square = self._make_move(move.chess_move)
                special_case = self._check_special_cases()
                if captured_square is not None:
                    # If it was capture
                    return (
                        MoveAnnouncement.CAPTURE_DONE,
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
        elif move.question_type == QA.ASK_ANY:
            # Any Rule. Asking for any available pawn captures.
            # Possible to ask once a turn
            self.possible_to_ask.remove(KSMove(QA.ASK_ANY))
            if self._has_any_pawn_captures():
                self._must_use_pawns = True
                self._generate_possible_to_ask_list()
                return (
                    MoveAnnouncement.HAS_ANY,
                    None,
                    None
                )
            else:
                return (
                    MoveAnnouncement.NO_ANY,
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
        def same_rank(from_sq, to_sq):
            # Or same row
            return chess.rank_index(from_sq) == chess.rank_index(to_sq)

        def same_file(from_sq, to_sq):
            # Or same column
            return chess.file_index(from_sq) == chess.file_index(to_sq)

        def sw_ne_diagonal(from_sq, to_sq):
            # Or on one lower-left upper-right diagonal
            # Parallel to A1H8
            return ((chess.rank_index(from_sq) - chess.rank_index(to_sq)) ==
                    (chess.file_index(from_sq) - chess.file_index(to_sq)))

        def nw_se_diagonal(from_sq, to_sq):
            # Or on one upper-left lower-right diagonal
            # Parallel to A8H1
            return ((chess.rank_index(from_sq) - chess.rank_index(to_sq)) ==
                    -(chess.file_index(from_sq) - chess.file_index(to_sq)))

        def is_short_diagonal(from_sq, to_sq):
            '''
            return True is diagonal is short
            '''
            if (((to_sq // 8 <= 3) and (to_sq % 8 <= 3)) or
                    ((to_sq // 8 > 3) and (to_sq % 8 > 3))):
                # This means that King is in lower-left quadrant or
                # in upper-right quadrant
                # In this quadrants NW_SE_diagonals are shortest
                if nw_se_diagonal(from_sq, to_sq):
                    return True
                elif sw_ne_diagonal(from_sq, to_sq):
                    return False
                else:
                    raise KeyError
            else:
                # Other two quadrants. And diagonals are vise-versa.
                if nw_se_diagonal(from_sq, to_sq):
                    return False
                elif sw_ne_diagonal(from_sq, to_sq):
                    return True
                else:
                    raise KeyError

        if self.board.is_game_over():
            if self.board.is_fivefold_repetition():
                return SpecialCaseAnnouncement.DRAW_FIVEFOLD
            if self.board.is_seventyfive_moves():
                return SpecialCaseAnnouncement.DRAW_SEVENTYFIVE
            if self.board.is_stalemate():
                return SpecialCaseAnnouncement.DRAW_STALEMATE
            if self.board.is_insufficient_material():
                return SpecialCaseAnnouncement.DRAW_INSUFFICIENT
            if self.board.is_checkmate():
                if self.board.result() == '1-0':
                    return SpecialCaseAnnouncement.CHECKMATE_WHITE_WINS
                elif self.board.result() == '0-1':
                    return SpecialCaseAnnouncement.CHECKMATE_BLACK_WINS

        if self.board.is_check():
            sq = self.board.pieces(chess.KING, self.board.turn)
            king_square = sq.pop()
            attackers = self.board.attackers(not self.board.turn, king_square)
            attackers_squares = list(attackers)
            if len(attackers_squares) > 1:
                return SpecialCaseAnnouncement.CHECK_DOUBLE
            elif len(attackers_squares) == 1:
                attacker_square = attackers_squares[0]
                if same_file(attacker_square, king_square):
                    return SpecialCaseAnnouncement.CHECK_FILE
                elif same_rank(attacker_square, king_square):
                    return SpecialCaseAnnouncement.CHECK_RANK
                elif (sw_ne_diagonal(attacker_square, king_square) or
                      nw_se_diagonal(attacker_square, king_square)):
                    if is_short_diagonal(attacker_square, king_square):
                        return SpecialCaseAnnouncement.CHECK_SHORT_DIAGONAL
                    else:
                        return SpecialCaseAnnouncement.CHECK_LONG_DIAGONAL
                else:
                    return SpecialCaseAnnouncement.CHECK_KNIGHT
            else:
                raise RuntimeError
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
        captured_square = None
        if self.board.is_capture(move):
            captured_square = self._get_captured_square(move)
        self.board.push(move)
        self._generate_possible_to_ask_list()
        return captured_square

    def _has_any_pawn_captures(self):
        pawn_squares = self.board.pieces(chess.PAWN, self.board.turn)
        for move in self.board.legal_moves:
            if move.from_square in pawn_squares:
                if self.board.is_capture(move):
                    return True
        return False

    def _is_legal_move(self, move):
        return move in self.board.legal_moves

    def _generate_possible_to_ask_list(self):
        # Very slow. :(
        # Make a board that current player see
        players_board = self.board.copy()
        for square in chess.SQUARES:
            if players_board.piece_at(square) is not None:
                if players_board.piece_at(square).color is not self.board.turn:
                    players_board.remove_piece_at(square)
        # Now players_board is equal to board that current player see
        possibilities = list()
        # First collect all possible moves keeping in mind castling rules
        if not self._must_use_pawns:
            possibilities.extend([
                KSMove(QA.COMMON, chess_move)
                for chess_move in players_board.legal_moves
            ])
            # Always possible to ask ANY?
            possibilities.append(KSMove(QA.ASK_ANY))
        # Second add possible pawn captures
        for square in chess.SQUARES:
            if players_board.piece_at(square) is not None:
                if players_board.piece_type_at(square) == chess.PAWN:
                    possibilities.extend([
                        KSMove(QA.COMMON, chess.Move(square, attacked))
                        for attacked in list(players_board.attacks(square))
                        if players_board.piece_at(attacked) is None
                    ])
        # And return with no dups
        self.possible_to_ask = list(set(possibilities))

    def is_possible_to_ask(self, move):
        return move in self.possible_to_ask
