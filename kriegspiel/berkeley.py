# -*- coding: utf-8 -*-

import enum

import chess

from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA

from kriegspiel.move import KriegspielScoresheet as KSSS


HALFMOVE_CLOCK_LIMIT = 2000


class BerkeleyGame(object):
    """
    Main class for Berkley Kriegspiel variant. Supports two main variants:
    with ANY rule and without ANY rule. If any_rule = True — means Berkeley + Any
    This class should be on the server's side as has info about all pieces on the
    board.

    Communication with this class must be in the form of questions —
    KriegspielMove(s) with QuestionAnnouncement(s).

    As the response this class with respond with KriegspielAnswer(s), with
    MainAnnouncement(s) and SpecialCaseAnnouncement.
    """

    def __init__(self, any_rule=True):
        super(BerkeleyGame).__init__()
        self._any_rule = any_rule
        self._board = chess.Board()
        self._must_use_pawns = False
        self._game_over = False
        self._generate_possible_to_ask_list()
        self._whites_scoresheet = KSSS(chess.WHITE)
        self._blacks_scoresheet = KSSS(chess.BLACK)

    def ask_for(self, move):
        """
        The main public method for asking questions to the referee in the
        form of KriegspielMove(s). This method returns KriegspielAnswer(s).
        If the answer is in kriegspiel.move.MOVE_DONE then the next question
        must be from a different player, else from the same player. Or it can
        be SpecialCaseAnnoucement of CHECKMATE_* or DRAW_*.
        """
        if not isinstance(move, KSMove):
            raise TypeError
        # Get the main response of the referee
        result = self._ask_for(move)
        # Record the move if it was legit question.
        if result.main_announcement != MA.IMPOSSIBLE_TO_ASK:
            self._record_the_move(move, result)
        # Regenerate possible to asking list if a move is done
        if result.move_done:
            self._generate_possible_to_ask_list()
        # Remove non-pawn-captures if there are any pawn captures.
        # As you MUST do a pawn-capture move when you got positive
        # response from the referee on ASK_ANY.
        if result.main_announcement == MA.HAS_ANY:
            self._possible_to_ask = list(
                # Yes, it could be simplified from the first glance, but it will be incorrect.
                # As some pawn moves were alredy potentially asked.
                set(self._possible_to_ask)
                - (set(self._possible_to_ask) - set(self._generate_posible_pawn_captures()))
            )
        # Remove pawn captures if there is no pawn captures.
        if result.main_announcement == MA.NO_ANY:
            self._possible_to_ask = list(set(self._possible_to_ask) - set(self._generate_posible_pawn_captures()))
        # Possible to ask about a move only once
        if result.main_announcement in (MA.ILLEGAL_MOVE, MA.NO_ANY):
            # For `has any` already deleted
            self._possible_to_ask.remove(move)
        return result

    def _ask_for(self, move):
        """
        return (MoveAnnouncement, captured_square, SpecialCaseAnnouncement)
        """
        # If a player asks for a non-sense move. Stop it.
        if move not in self.possible_to_ask:
            return KSAnswer(MA.IMPOSSIBLE_TO_ASK)

        if move.question_type == QA.COMMON:
            # Player asks about a common move
            if self._is_legal_move(move.chess_move):
                # Move is legal in normal chess
                # Perform normal move
                captured_square = self._make_move(move.chess_move)
                special_case = self._check_special_cases()
                if captured_square is not None:
                    # If it was capture
                    return KSAnswer(MA.CAPTURE_DONE, capture_at_square=captured_square, special_announcement=special_case)
                # If it was a regular move, and NO captures
                return KSAnswer(MA.REGULAR_MOVE, special_announcement=special_case)
            # If a move is illegal from the referee's perspective. But it's
            # was a possible move from asking player's perspective.
            # IMPORTANT: That's a new info for both players. Hence must be announced.
            return KSAnswer(MA.ILLEGAL_MOVE)
        elif move.question_type == QA.ASK_ANY:
            # Any Rule. Asking for any available pawn captures.
            # Possible to ask once a turn
            if self._has_any_pawn_captures():
                self._must_use_pawns = True
                return KSAnswer(MA.HAS_ANY)
            else:
                return KSAnswer(MA.NO_ANY)

    def _record_the_move(self, move, answer):
        current_turn = self._board.turn
        if answer.move_done:
            current_turn = not current_turn
        if current_turn == chess.WHITE:
            self._whites_scoresheet.record_move_own(move, answer)
            self._blacks_scoresheet.record_move_opponent(move.question_type, answer)
        else:
            self._blacks_scoresheet.record_move_own(move, answer)
            self._whites_scoresheet.record_move_opponent(move.question_type, answer)

    def is_game_over(self):
        """
        Returns True if game already ended.
        """
        # If it is already over.
        if self._game_over:
            return True
        # Or it is new condition.
        if (
            self._board.is_stalemate()
            or self._board.is_insufficient_material()
            or self._board.is_checkmate()
            or self._board.halfmove_clock == HALFMOVE_CLOCK_LIMIT
        ):
            self._game_over = True
            return True
        return False

    def _check_special_cases(self):
        """
        Method to identify kind of SpecialCaseAnnouncement if any.
        If not a SpecialCase, then SpecialCaseAnnouncement.NONE.
        """

        def same_rank(from_sq, to_sq):
            # Or the same row
            return chess.square_rank(from_sq) == chess.square_rank(to_sq)

        def same_file(from_sq, to_sq):
            # Or the same column
            return chess.square_file(from_sq) == chess.square_file(to_sq)

        def sw_ne_diagonal(from_sq, to_sq):
            # Or on one lower-left upper-right diagonal
            # Parallel to A1H8 / South-West – North-East
            return (chess.square_rank(from_sq) - chess.square_rank(to_sq)) == (
                chess.square_file(from_sq) - chess.square_file(to_sq)
            )

        def nw_se_diagonal(from_sq, to_sq):
            # Or on one upper-left lower-right diagonal
            # Parallel to A8H1 / North-West — South-East
            return (chess.square_rank(from_sq) - chess.square_rank(to_sq)) == -(
                chess.square_file(from_sq) - chess.square_file(to_sq)
            )

        def is_short_diagonal(from_sq, to_sq):
            """
            return True if the diagonal is short
            """
            if ((chess.square_rank(to_sq) <= 3) and (chess.square_file(to_sq) <= 3)) or (
                (chess.square_rank(to_sq) > 3) and (chess.square_file(to_sq) > 3)
            ):
                # This means that King is in the lower-left quadrant or
                # in the upper-right quadrant
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
            # Identify the type of check. That will be announced.
            if same_file(attacker_square, king_square):
                return SCA.CHECK_FILE
            elif same_rank(attacker_square, king_square):
                return SCA.CHECK_RANK
            elif sw_ne_diagonal(attacker_square, king_square) or nw_se_diagonal(attacker_square, king_square):
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
                if self._board.result() == "1-0":
                    return SCA.CHECKMATE_WHITE_WINS
                elif self._board.result() == "0-1":
                    return SCA.CHECKMATE_BLACK_WINS
            if self._board.halfmove_clock == HALFMOVE_CLOCK_LIMIT:
                return SCA.DRAW_TOOMANYREVERSIBLEMOVES

        if self._board.is_check():
            sq = self._board.pieces(chess.KING, self._board.turn)
            king_square = sq.pop()
            attackers = self._board.attackers(not self._board.turn, king_square)
            attackers_squares = list(attackers)
            if len(attackers_squares) == 2:
                # If it's a double check.
                first = kind_of_check(attackers_squares[0], king_square)
                second = kind_of_check(attackers_squares[1], king_square)
                return SCA.CHECK_DOUBLE, [first, second]
            elif len(attackers_squares) == 1:
                # If it's a single check
                attacker_square = attackers_squares[0]
                return kind_of_check(attacker_square, king_square)
            else:  # pragma: no cover
                raise RuntimeError
        return SCA.NONE

    def _get_captured_square(self, move):
        """
        A square with capture will be announced.
        """
        if not self._board.is_en_passant(move):
            return move.to_square
        else:
            if self._board.turn == chess.WHITE:
                return move.to_square - 8
            else:
                return move.to_square + 8

    def _make_move(self, move):
        """
        Make the move on the referee's board
        and return square with capture.
        """
        self._must_use_pawns = False
        captured_square = None
        if self._board.is_capture(move):
            captured_square = self._get_captured_square(move)
        self._board.push(move)
        return captured_square

    def _has_any_pawn_captures(self):
        """
        To check if HAS_ANY pawn captures.
        """
        pawn_squares = self._board.pieces(chess.PAWN, self._board.turn)
        for move in self._board.legal_moves:
            if move.from_square in pawn_squares:
                if self._board.is_capture(move):
                    return True
        return False

    def _is_legal_move(self, move):
        return move in self._board.legal_moves

    def _prepare_players_board(self):
        """
        Make board that is visible for the current player.
        """
        # Make a copy of the FULL board (referee's board)
        players_board = self._board.copy(stack=False)
        # Remove all pieces belonging not to the current player
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
                        possibilities.extend(
                            [
                                KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.QUEEN)),
                                KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.BISHOP)),
                                KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.KNIGHT)),
                                KSMove(QA.COMMON, chess.Move(square, attacked, promotion=chess.ROOK)),
                            ]
                        )
                    else:
                        # If capture is not promotion for pawn
                        possibilities.append(KSMove(QA.COMMON, chess.Move(square, attacked)))
        return possibilities

    def _generate_possible_to_ask_list(self):
        # Very slow. :(
        if self._game_over:
            self._possible_to_ask = list()
            return
        # Make the board that the current player sees
        self._prepare_players_board()
        # Now players_board is equal to the board that the current player sees
        possibilities = list()
        # First collect all possible moves keeping in mind castling rules.
        # Castling rules are kept as it is generated by the referee's board,
        # which contains info about previous moves.
        possibilities.extend([KSMove(QA.COMMON, chess_move) for chess_move in self._players_board.legal_moves])
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
