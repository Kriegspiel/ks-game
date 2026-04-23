# -*- coding: utf-8 -*-

import chess

from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA

from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA

from kriegspiel.move import KriegspielScoresheet as KSSS
from kriegspiel.rulesets import resolve_ruleset_policy
from kriegspiel.snapshot import KriegspielGameSnapshot
from kriegspiel.snapshot import move_stack_from_scoresheets
from kriegspiel.serialization import save_game_to_json, load_game_from_json


HALFMOVE_CLOCK_LIMIT = 2000


class KriegspielGame(object):
    """
    Shared hidden-board Kriegspiel referee engine.

    Ruleset-specific behavior such as Berkeley `ASK_ANY`, Cincinnati binary
    pawn-capture announcements, or Wild 16 pawn-try counts is delegated to a
    policy layer. Variant-named wrappers like `BerkeleyGame`, `CincinnatiGame`,
    and `Wild16Game` build on this class.

    Communication with this class must be in the form of questions —
    KriegspielMove(s) with QuestionAnnouncement(s).

    As the response this class with respond with KriegspielAnswer(s), with
    MainAnnouncement(s) and SpecialCaseAnnouncement.
    """

    def __init__(self, any_rule=None, ruleset=None):
        """
        Initialize a new Kriegspiel referee game.
        
        Args:
            any_rule: Legacy compatibility flag for Berkeley+Any. When omitted,
                     Berkeley+Any remains the default.
            ruleset: Explicit ruleset identifier. Supported values are
                     `berkeley`, `berkeley_any`, `cincinnati`, and `wild16`.
        """
        super().__init__()
        self._ruleset = resolve_ruleset_policy(ruleset=ruleset, any_rule=any_rule)
        self._any_rule = self._ruleset.allow_ask_any
        self._board = chess.Board()
        self._must_use_pawns = False
        self._game_over = False
        self._possible_to_ask = []
        self._possible_to_ask_set = set()
        self._generate_possible_to_ask_list()
        self._whites_scoresheet = KSSS(chess.WHITE)
        self._blacks_scoresheet = KSSS(chess.BLACK)

    def ask_for(self, move):
        """
        Ask the referee a question about a potential move.
        
        This is the main public interface for interacting with the Kriegspiel referee.
        Players submit KriegspielMove questions and receive KriegspielAnswer responses
        containing the outcome and any special announcements.
        
        Args:
            move: KriegspielMove object representing either a COMMON move question
                 (asking if a specific chess move is legal) or an ASK_ANY question
                 (asking if there are any pawn captures available).
        
        Returns:
            KriegspielAnswer: Contains the main announcement (MOVE_DONE, ILLEGAL_MOVE, etc.),
                            any capture information, and special case announcements like
                            CHECK, CHECKMATE, or DRAW conditions.
        
        Raises:
            TypeError: If move is not a KriegspielMove object.
            
        Note:
            - If the answer is MOVE_DONE, the next question must be from the other player
            - If the answer is ILLEGAL_MOVE or IMPOSSIBLE_TO_ASK, the same player continues
            - After HAS_ANY response, player must make a pawn capture move
        """
        if not isinstance(move, KSMove):
            raise TypeError("move must be a KriegspielMove")
        # Get the main response of the referee
        result = self._ask_for(move)
        # Record the move if it was legit question.
        if result.main_announcement != MA.IMPOSSIBLE_TO_ASK:
            self._record_the_move(move, result)
        # Regenerate possible to asking list if a move is done
        if result.move_done:
            self._generate_possible_to_ask_list()
        self._ruleset.apply_post_answer_constraints(self, result)
        if self._ruleset.should_discard_attempt(move, result):
            self._discard_possible_to_ask(move)
        return result

    def _ask_for(self, move):
        """
        return (MoveAnnouncement, captured_square, SpecialCaseAnnouncement)
        """
        if move.question_type == QA.COMMON:
            if move not in self._possible_to_ask_set:
                return KSAnswer(self._ruleset.classify_impossible_common_attempt())
            # Player asks about a common move
            if self._is_legal_move(move.chess_move):
                # Move is legal in normal chess
                # Perform normal move
                captured_square, captured_piece_announcement = self._make_move(move.chess_move)
                special_case = self._check_special_cases()
                next_turn_pawn_tries = self._ruleset.next_turn_pawn_tries(self)
                next_turn_has_pawn_capture = self._ruleset.next_turn_has_pawn_capture(self)
                answer_kwargs = {"special_announcement": special_case}
                if next_turn_pawn_tries is not None:
                    answer_kwargs["next_turn_pawn_tries"] = next_turn_pawn_tries
                if next_turn_has_pawn_capture is not None:
                    answer_kwargs["next_turn_has_pawn_capture"] = next_turn_has_pawn_capture
                if captured_square is not None:
                    # If it was capture
                    answer_kwargs["capture_at_square"] = captured_square
                    if captured_piece_announcement is not None:
                        answer_kwargs["captured_piece_announcement"] = captured_piece_announcement
                    return KSAnswer(MA.CAPTURE_DONE, **answer_kwargs)
                # If it was a regular move, and NO captures
                return KSAnswer(MA.REGULAR_MOVE, **answer_kwargs)
            # If a move is illegal from the referee's perspective. But it's
            # was a possible move from asking player's perspective.
            return KSAnswer(MA.ILLEGAL_MOVE)
        if move not in self._possible_to_ask_set:
            return KSAnswer(MA.IMPOSSIBLE_TO_ASK)
        policy_answer = self._ruleset.handle_special_question(self, move)
        if policy_answer is not None:
            return policy_answer
        raise ValueError(f"Unsupported question type for ruleset {self.ruleset_id}: {move.question_type}")

    def _record_the_move(self, move, answer):
        current_turn = self._board.turn
        if answer.move_done:
            current_turn = not current_turn
        if current_turn == chess.WHITE:
            self._whites_scoresheet.record_move_own(move, answer)
            if self._ruleset.should_record_opponent_answer(move, answer):
                self._blacks_scoresheet.record_move_opponent(move.question_type, answer)
        else:
            self._blacks_scoresheet.record_move_own(move, answer)
            if self._ruleset.should_record_opponent_answer(move, answer):
                self._whites_scoresheet.record_move_opponent(move.question_type, answer)

    def is_game_over(self):
        """
        Check if the game has ended and update game state accordingly.
        
        Evaluates current board position for terminal conditions including
        checkmate, stalemate, insufficient material, and repetition rules.
        Updates the internal _game_over flag when a terminal state is detected.
        
        Returns:
            bool: True if the game has ended due to any terminal condition,
                 False if the game can continue.
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
                    raise RuntimeError("Expected attacker and king to share a diagonal")
            else:
                # Other two quadrants. And diagonals are vise-versa.
                if nw_se_diagonal(from_sq, to_sq):
                    return False
                elif sw_ne_diagonal(from_sq, to_sq):
                    return True
                else:  # pragma: no cover
                    raise RuntimeError("Expected attacker and king to share a diagonal")

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
                result = self._board.result()
                if result == "1-0":
                    return SCA.CHECKMATE_WHITE_WINS
                if result == "0-1":
                    return SCA.CHECKMATE_BLACK_WINS
                raise RuntimeError("Unexpected checkmate result")  # pragma: no cover
            if self._board.halfmove_clock == HALFMOVE_CLOCK_LIMIT:
                return SCA.DRAW_TOOMANYREVERSIBLEMOVES
            raise RuntimeError("Expected a terminal announcement for a finished game")  # pragma: no cover

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

    def _get_captured_piece(self, move):
        """Return the piece removed by a capture before the move is pushed."""
        if not self._board.is_capture(move):
            return None
        captured_square = self._get_captured_square(move)
        return self._board.piece_at(captured_square)

    def _make_move(self, move):
        """
        Make the move on the referee's board
        and return capture details.
        """
        self._must_use_pawns = False
        captured_square = None
        captured_piece_announcement = None
        if self._board.is_capture(move):
            captured_square = self._get_captured_square(move)
            captured_piece = self._get_captured_piece(move)
            captured_piece_announcement = self._ruleset.captured_piece_announcement_for(captured_piece)
        self._board.push(move)
        return captured_square, captured_piece_announcement

    def _legal_pawn_capture_moves(self):
        """Return legal pawn captures for the active player in the true position."""
        pawn_squares = self._board.pieces(chess.PAWN, self._board.turn)
        return [
            move
            for move in self._board.legal_moves
            if move.from_square in pawn_squares and self._board.is_capture(move)
        ]

    def _count_legal_pawn_captures(self):
        """Count legal pawn captures for the active player in the true position."""
        return len(self._legal_pawn_capture_moves())

    def _has_any_pawn_captures(self):
        """
        Check if the current player has any possible pawn captures.
        
        Used to answer ASK_ANY questions about whether pawn captures are available.
        
        Returns:
            bool: True if there are any legal pawn capture moves available,
                 False if no pawn captures are possible.
        """
        return self._count_legal_pawn_captures() > 0

    def _is_legal_move(self, move):
        """
        Check if a chess move is legal in the current position.
        
        Args:
            move: python-chess Move object to validate
            
        Returns:
            bool: True if the move is legal, False otherwise.
        """
        return self._board.is_legal(move)

    def _build_players_board(self):
        """
        Create the board state visible to the current player.
        
        Generates a copy of the main board with only the current player's pieces
        visible, simulating what the player can see in Kriegspiel where opponent
        pieces are hidden.
        """
        # Make a copy of the FULL board (referee's board)
        players_board = self._board.copy(stack=False)
        active_color = self._board.turn
        # Remove all pieces belonging not to the current player
        for square, piece in self._board.piece_map().items():
            if piece.color != active_color:
                players_board.remove_piece_at(square)
        return players_board

    def _generate_possible_pawn_captures(self):
        """
        Generate all possible pawn capture moves for the current player.
        
        Returns:
            List[KriegspielMove]: All possible pawn captures including regular
                                captures and captures with promotion to all piece types.
        """
        possibilities = list()
        active_color = self._board.turn
        for square in self._board.pieces(chess.PAWN, active_color):
            for attacked in self._board.attacks(square):
                if self._board.color_at(attacked) == active_color:
                    continue
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

    def _set_possible_to_ask(self, possibilities):
        self._possible_to_ask_set = set(possibilities)
        self._possible_to_ask = list(self._possible_to_ask_set)

    def _discard_possible_to_ask(self, move):
        if move not in self._possible_to_ask_set:
            return
        self._possible_to_ask_set.remove(move)
        try:
            self._possible_to_ask.remove(move)
        except ValueError:  # pragma: no cover
            self._possible_to_ask = list(self._possible_to_ask_set)

    def _generate_possible_to_ask_list(self):
        """
        Generate list of all possible questions/moves for the current player.
        
        This method creates the complete list of legal questions the current player
        can ask, including regular moves from their visible board state, possible
        pawn captures, and ASK_ANY questions if the any_rule is enabled.
        
        Note:
            Variant-specific additions such as `ASK_ANY` are injected by the
            active ruleset policy instead of being hard-coded here.
        """
        if self._game_over:
            self._set_possible_to_ask(set())
            return
        # Make the board that the current player sees
        players_board = self._build_players_board()
        # First collect all possible moves keeping in mind castling rules.
        # Castling rules are kept as it is generated by the referee's board,
        # which contains info about previous moves.
        possibilities = {KSMove(QA.COMMON, chess_move) for chess_move in players_board.legal_moves}
        self._ruleset.add_special_questions(possibilities)
        # Second add possible pawn captures
        possibilities.update(self._generate_possible_pawn_captures())
        self._set_possible_to_ask(possibilities)

    @property
    def possible_to_ask(self):
        """
        Get list of currently possible moves and questions for the active player.
        
        Returns:
            List[KriegspielMove]: All legal moves and questions the current player
                                can ask, including regular moves, pawn captures,
                                and ASK_ANY questions (if any_rule is enabled).
        """
        return self._possible_to_ask

    @property
    def game_over(self):
        """
        Check if the game has ended.
        
        Returns:
            bool: True if the game is over due to checkmate, stalemate,
                 or draw conditions. False if the game is still active.
        """
        return self._game_over

    @property
    def any_rule(self):
        """Backward-compatible public flag for Berkeley+Any behavior."""
        return self._any_rule

    @property
    def ruleset_id(self):
        """Explicit ruleset identifier for snapshot and serialization APIs."""
        return self._ruleset.identifier

    @property
    def current_turn_pawn_tries(self):
        """
        Get the Wild 16 style pawn-capture count for the current player to move.

        Returns:
            int or None: Legal pawn-capture count when the active ruleset announces it.
        """
        return self._ruleset.next_turn_pawn_tries(self)

    @property
    def current_turn_has_pawn_capture(self):
        """
        Get the Cincinnati-style binary pawn-capture announcement for the player to move.

        Returns:
            bool or None: Pawn-capture availability when the active ruleset announces it.
        """
        return self._ruleset.next_turn_has_pawn_capture(self)

    @property
    def must_use_pawns(self):
        """
        Check if the current player must make a pawn capture move.
        
        This is set to True after a player receives HAS_ANY response,
        forcing them to make one of the available pawn captures.
        
        Returns:
            bool: True if player must capture with a pawn, False otherwise.
        """
        return self._must_use_pawns

    @property
    def turn(self):
        """
        Get whose turn it is to move.
        
        Returns:
            bool: chess.WHITE (True) if it's White's turn,
                 chess.BLACK (False) if it's Black's turn.
        """
        return self._board.turn

    def is_possible_to_ask(self, move):
        """
        Check if a specific move/question is currently legal to ask.
        
        Args:
            move: KriegspielMove object to check
            
        Returns:
            bool: True if the move is in the current list of possible questions,
                 False if it's not allowed or has already been asked.
        """
        return move in self._possible_to_ask_set

    def save_game(self, filename):
        """
        Save the current game state to a JSON file.
        
        Args:
            filename: Path to the file where the game state will be saved
        """
        save_game_to_json(self, filename)

    def snapshot(self):
        """Return a public snapshot of the current game state."""
        return KriegspielGameSnapshot(
            ruleset_id=self.ruleset_id,
            any_rule=self.any_rule,
            board_fen=self._board.fen(),
            move_stack=tuple(move.uci() for move in self._board.move_stack),
            must_use_pawns=self._must_use_pawns,
            game_over=self._game_over,
            possible_to_ask=tuple(self._possible_to_ask),
            white_scoresheet=self._whites_scoresheet.snapshot(),
            black_scoresheet=self._blacks_scoresheet.snapshot(),
        )

    @classmethod
    def from_snapshot(cls, snapshot):
        """Build a KriegspielGame from a validated public snapshot."""
        if not isinstance(snapshot, KriegspielGameSnapshot):
            raise TypeError("snapshot must be a KriegspielGameSnapshot")

        try:
            chess.Board(snapshot.board_fen)
        except ValueError as exc:
            raise ValueError(f"Invalid board FEN: {snapshot.board_fen}") from exc

        board = chess.Board()
        try:
            for move_uci in snapshot.move_stack:
                board.push_uci(move_uci)
        except ValueError as exc:
            raise ValueError(f"Invalid move_stack entry: {move_uci}") from exc

        if board.fen() != snapshot.board_fen:
            raise ValueError("Serialized move_stack does not match board_fen")

        derived_move_stack = move_stack_from_scoresheets(
            snapshot.white_scoresheet, snapshot.black_scoresheet
        )
        if derived_move_stack != snapshot.move_stack:
            raise ValueError("Scoresheet-derived moves do not match move_stack")

        game = cls(ruleset=snapshot.ruleset_id)
        game._board = board
        game._must_use_pawns = snapshot.must_use_pawns
        game._game_over = snapshot.game_over
        game._whites_scoresheet = KSSS.from_snapshot(snapshot.white_scoresheet)
        game._blacks_scoresheet = KSSS.from_snapshot(snapshot.black_scoresheet)
        if snapshot.possible_to_ask is None:
            game._generate_possible_to_ask_list()
            if game._must_use_pawns:
                game._set_possible_to_ask(game._generate_possible_pawn_captures())
        else:
            game._set_possible_to_ask(snapshot.possible_to_ask)
        return game

    @classmethod
    def load_game(cls, filename):
        """
        Load a game state from a JSON file.
        
        Args:
            filename: Path to the file containing the saved game state
            
        Returns:
            KriegspielGame: New game instance with restored state
        """
        return cls.from_snapshot(load_game_from_json(filename).snapshot())
