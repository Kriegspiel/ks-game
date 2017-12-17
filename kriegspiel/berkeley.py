# -*- coding: utf-8 -*-

import enum

import chess

from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA


HALFMOVE_CLOCK_LIMIT = 2000


class BerkeleyGame(object):
    '''If any_rule = True – means Berkeley + Any'''

    def __init__(self, any_rule=True):
        super(BerkeleyGame).__init__()
        self._any_rule = any_rule
        self._board = chess.Board()
        self._must_use_pawns = False
        self._game_over = False
        self._generate_possible_to_ask_list()

    def ask_for(self, move):
        if not isinstance(move, KSMove):
            raise TypeError
        result = self._ask_for(move)
        # Regenerate possbile to ask list if move is done
        if result.move_done:
            self._generate_possible_to_ask_list()
        # Remove non-pawn-captures is there is any pawn captures
        if result.main_announcement == MA.HAS_ANY:
            self._possible_to_ask = list(
                        set(self._possible_to_ask) -
                    (set(self._possible_to_ask) - set(self._generate_posible_pawn_captures()))
            )
        # Remove pawn captures is there is no pawn captures
        if result.main_announcement == MA.NO_ANY:
            self._possible_to_ask = list(set(self._possible_to_ask) - set(self._generate_posible_pawn_captures()))
        # Possible to ask about a move only once
        if result.main_announcement in (MA.ILLEGAL_MOVE, MA.NO_ANY):
            # For `has any` already deleted
            self._possible_to_ask.remove(move)
        return result

    def _ask_for(self, move):
        '''
        return (MoveAnnouncement, captured_square, SpecialCaseAnnouncement)
        '''
        if move not in self.possible_to_ask:
            return KSAnswer(MA.IMPOSSIBLE_TO_ASK)

        if move.question_type == QA.COMMON:
            # Player asks about common move
            if self._is_legal_move(move.chess_move):
                # Move is legal in normal chess
                # Perform normal move
                captured_square = self._make_move(move.chess_move)
                special_case = self._check_special_cases()
                if captured_square is not None:
                    # If it was capture
                    return KSAnswer(MA.CAPTURE_DONE,
                        capture_at_square=captured_square,
                        special_announcement=special_case
                    )
                # If it was regular move
                return KSAnswer(MA.REGULAR_MOVE,
                    special_announcement=special_case
                )
            # If move is illegal
            return KSAnswer(MA.ILLEGAL_MOVE)
        elif move.question_type == QA.ASK_ANY:
            # Any Rule. Asking for any available pawn captures.
            # Possible to ask once a turn
            if self._has_any_pawn_captures():
                self._must_use_pawns = True
                return KSAnswer(MA.HAS_ANY)
            else:
                return KSAnswer(MA.NO_ANY)

    def is_game_over(self):
        if self._game_over:
            return True
        if (self._board.is_stalemate() or
                self._board.is_insufficient_material() or
                self._board.is_checkmate() or
                self._board.halfmove_clock == HALFMOVE_CLOCK_LIMIT):
            self._game_over = True
            return True
        return False

    def _check_special_cases(self):
        def same_rank(from_sq, to_sq):
            # Or same row
            return chess.square_rank(from_sq) == chess.square_rank(to_sq)
        def same_file(from_sq, to_sq):
            # Or same column
            return chess.square_file(from_sq) == chess.square_file(to_sq)
        def sw_ne_diagonal(from_sq, to_sq):
            # Or on one lower-left upper-right diagonal
            # Parallel to A1H8
            return ((chess.square_rank(from_sq) - chess.square_rank(to_sq)) ==
                    (chess.square_file(from_sq) - chess.square_file(to_sq)))
        def nw_se_diagonal(from_sq, to_sq):
            # Or on one upper-left lower-right diagonal
            # Parallel to A8H1
            return ((chess.square_rank(from_sq) - chess.square_rank(to_sq)) ==
                    -(chess.square_file(from_sq) - chess.square_file(to_sq)))
        def is_short_diagonal(from_sq, to_sq):
            '''
            return True is diagonal is short
            '''
            if (((chess.square_rank(to_sq) <= 3) and (chess.square_file(to_sq) <= 3)) or
                    ((chess.square_rank(to_sq) > 3) and (chess.square_file(to_sq) > 3))):
                # This means that King is in lower-left quadrant or
                # in upper-right quadrant
                # In this quadrants NW_SE_diagonals are shortest
                if nw_se_diagonal(from_sq, to_sq):
                    return True
                elif sw_ne_diagonal(from_sq, to_sq):
                    return False
                else:  # pragma: no cover
                    raise KeyError
            else:
                # Other two quadrants. And diagonals are vise-versa.
                if nw_se_diagonal(from_sq, to_sq):
                    return False
                elif sw_ne_diagonal(from_sq, to_sq):
                    return True
                else:  # pragma: no cover
                    raise KeyError
        def kind_of_check(attacker_square, king_square):
            if same_file(attacker_square, king_square):
                return SCA.CHECK_FILE
            elif same_rank(attacker_square, king_square):
                return SCA.CHECK_RANK
            elif (sw_ne_diagonal(attacker_square, king_square) or
                  nw_se_diagonal(attacker_square, king_square)):
                if is_short_diagonal(attacker_square, king_square):
                    return SCA.CHECK_SHORT_DIAGONAL
                else:
                    return SCA.CHECK_LONG_DIAGONAL
            else:
                return SCA.CHECK_KNIGHT

        if self.is_game_over():
            self._game_over = True
            if self._board.is_stalemate():
                return SCA.DRAW_STALEMATE
            if self._board.is_insufficient_material():
                return SCA.DRAW_INSUFFICIENT
            if self._board.is_checkmate():
                if self._board.result() == '1-0':
                    return SCA.CHECKMATE_WHITE_WINS
                elif self._board.result() == '0-1':
                    return SCA.CHECKMATE_BLACK_WINS
            if self._board.halfmove_clock == HALFMOVE_CLOCK_LIMIT:
                return SCA.DRAW_TOOMANYREVERSIBLEMOVES

        if self._board.is_check():
            sq = self._board.pieces(chess.KING, self._board.turn)
            king_square = sq.pop()
            attackers = self._board.attackers(not self._board.turn, king_square)
            attackers_squares = list(attackers)
            if len(attackers_squares) == 2:
                first = kind_of_check(attackers_squares[0], king_square)
                second = kind_of_check(attackers_squares[1], king_square)
                return SCA.CHECK_DOUBLE, [first, second]
            elif len(attackers_squares) == 1:
                attacker_square = attackers_squares[0]
                return kind_of_check(attacker_square, king_square)
            else:  # pragma: no cover
                raise RuntimeError
        return SCA.NONE

    def _get_captured_square(self, move):
        if not self._board.is_en_passant(move):
            return move.to_square
        else:
            if self._board.turn == chess.WHITE:
                return move.to_square - 8
            else:
                return move.to_square + 8

    def _make_move(self, move):
        self._must_use_pawns = False
        captured_square = None
        if self._board.is_capture(move):
            captured_square = self._get_captured_square(move)
        self._board.push(move)
        return captured_square

    def _has_any_pawn_captures(self):
        pawn_squares = self._board.pieces(chess.PAWN, self._board.turn)
        for move in self._board.legal_moves:
            if move.from_square in pawn_squares:
                if self._board.is_capture(move):
                    return True
        return False

    def _is_legal_move(self, move):
        return move in self._board.legal_moves

    def _prepare_players_board(self):
        players_board = self._board.copy(stack=False)
        for square in chess.SQUARES:
            if players_board.piece_at(square) is not None:
                if players_board.piece_at(square).color is not self._board.turn:
                    players_board.remove_piece_at(square)
        self._players_board = players_board

    def _generate_posible_pawn_captures(self):
        possibilities = list()
        for square in list(self._board.pieces(chess.PAWN, self._board.turn)):
            for attacked in list(self._players_board.attacks(square)):
                if self._players_board.piece_at(attacked) is None:
                    if chess.square_rank(attacked) in (0, 7):
                        # If capture is promotion for pawn.
                        possibilities.extend([
                            KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.QUEEN)),
                            KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.BISHOP)),
                            KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.KNIGHT)),
                            KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.ROOK))
                        ])
                    else:
                        # If capture is not promotion for pawn
                        possibilities.append(KSMove(QA.COMMON, chess.Move(square, attacked)))
        return possibilities

    def _generate_possible_to_ask_list(self):
        # Very slow. :(
        if self._game_over:
            self._possible_to_ask = list()
            return
        # Make a board that current player see
        self._prepare_players_board()
        # Now players_board is equal to board that current player see
        possibilities = list()
        # First collect all possible moves keeping in mind castling rules
        possibilities.extend([
            KSMove(QA.COMMON, chess_move)
            for chess_move in self._players_board.legal_moves
        ])
        if self._any_rule:
            # Always possible to ask ANY?
            possibilities.append(KSMove(QA.ASK_ANY))
        # Second add possible pawn captures
        possibilities.extend(self._generate_posible_pawn_captures())
        # And remove finally — remove duplicates
        self._possible_to_ask = list(set(possibilities))

    @property
    def possible_to_ask(self):
        return self._possible_to_ask

    @property
    def game_over(self):
        return self._game_over

    @property
    def must_use_pawns(self):
        return self._must_use_pawns

    @property
    def turn(self):
        return self._board.turn

    def is_possible_to_ask(self, move):
        return move in self.possible_to_ask
