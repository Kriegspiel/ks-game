# -*- coding: utf-8 -*-

import enum

import chess

_QUESTION_SORT_ORDER = {
    "ASK_ANY": 0,
    "COMMON": 1,
    "NONE": 2,
}


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
        """
        Initialize a Kriegspiel move question.
        
        Args:
            question_type: Type of question from QuestionAnnouncement enum.
                          Must be COMMON (for regular moves) or ASK_ANY (for pawn capture queries).
            chess_move: Required for COMMON questions. A python-chess Move object 
                       representing the desired move. Should be None for ASK_ANY questions.
        
        Raises:
            TypeError: If question_type is not a QuestionAnnouncement enum value,
                      or if chess_move is not provided for COMMON questions.
        """
        super(KriegspielMove, self).__init__()
        # Validation, that question type is from valid enum
        if not isinstance(question_type, QuestionAnnouncement):
            raise TypeError("question_type must be a QuestionAnnouncement")
        # Validation, that if the question is from common type,
        # then it should be valid chess move object
        if question_type == QuestionAnnouncement.COMMON and not isinstance(chess_move, chess.Move):
            raise TypeError("COMMON questions require a python-chess Move")
        self.question_type = question_type
        self.chess_move = chess_move

    def __str__(self):
        """
        Return string representation of the move.
        
        Returns:
            String in format "<KriegspielMove: {question_type}, move={chess_move}>"
        """
        return f"<KriegspielMove: {self.question_type}, move={self.chess_move}>"

    def _move_key(self):
        if self.chess_move is None:
            return None
        return (
            self.chess_move.from_square,
            self.chess_move.to_square,
            self.chess_move.promotion,
            self.chess_move.drop,
        )

    def _identity_key(self):
        return (self.question_type, self.chess_move)

    def _sort_key(self):
        return (
            _QUESTION_SORT_ORDER.get(self.question_type.name, self.question_type.value),
            self._move_key(),
        )

    def __repr__(self):
        """
        Return detailed string representation of the move.
        
        Returns:
            Same as __str__ for debugging purposes.
        """
        return self.__str__()

    def __eq__(self, other):
        """
        Check equality with another KriegspielMove.
        
        Two moves are equal if they have the same question_type and chess_move.
        
        Args:
            other: Object to compare with.
            
        Returns:
            True if moves are equivalent, False otherwise.
        """
        if not isinstance(other, KriegspielMove):
            return NotImplemented
        return self._identity_key() == other._identity_key()

    def __ne__(self, other):
        """
        Check inequality with another KriegspielMove.
        
        Args:
            other: Object to compare with.
            
        Returns:
            True if moves are not equivalent, False if they are equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __lt__(self, other):
        """
        Compare moves for sorting purposes.
        
        Comparison is based on structured move identity for stable ordering.
        
        Args:
            other: Another KriegspielMove to compare with.
            
        Returns:
            True if this move should be sorted before the other.
        """
        if not isinstance(other, KriegspielMove):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __hash__(self):
        """
        Generate hash value for the move.
        
        Enables KriegspielMove objects to be used in sets and as dictionary keys.
        Hash is based on the same structured identity used for equality.
        
        Returns:
            Integer hash value.
        """
        return hash(self._identity_key())


@enum.unique
class MainAnnouncement(enum.Enum):
    """
    There are 7 valid options for how to respond to Question Announcement
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
    4. CAPTURE_DONE — a move is valid and immediately done. Capture happened.
    5. NONSENSE — a move is impossible from the player's own information and
        should already be known to be impossible.

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
    NONSENSE = 6


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


@enum.unique
class CapturedPieceAnnouncement(enum.Enum):
    """Public capture detail for variants that announce pawn vs piece."""

    PAWN = 1
    PIECE = 2


class KriegspielAnswer(object):
    """
    Represents the referee's response to a Kriegspiel move question.
    
    This class encapsulates all information the referee provides after a player
    asks a question, including the main outcome, any captures, and special
    game state announcements like check or checkmate.
    """

    def __init__(self, main_announcement, **kwargs):
        """
        Initialize a Kriegspiel referee answer.
        
        Args:
            main_announcement: The primary response type from MainAnnouncement enum.
                             Values include MOVE_DONE, CAPTURE_DONE, ILLEGAL_MOVE, 
                             IMPOSSIBLE_TO_ASK, HAS_ANY, NO_ANY.
            **kwargs: Additional answer details:
                capture_at_square (int): Required for CAPTURE_DONE. Square number (0-63)
                                       where the capture occurred.
                captured_piece_announcement (CapturedPieceAnnouncement): Optional public
                                    capture detail for variants that distinguish pawn
                                    captures from other piece captures.
                special_announcement: Optional special game state from SpecialCaseAnnouncement
                                    enum. Can be a single value or tuple for double check.
                                    For CHECK_DOUBLE, provide (CHECK_DOUBLE, [check1, check2]).
                next_turn_pawn_tries (int): Optional Wild 16 style count of legal pawn
                                    captures available for the next player to move.
                next_turn_has_pawn_capture (bool): Optional Cincinnati-style binary
                                    pawn-capture announcement for the next player to move.
        
        Raises:
            TypeError: If main_announcement is not a MainAnnouncement enum value,
                      or if capture_at_square is not an integer when required.
            ValueError: If capture_at_square is outside valid range (0-63),
                       or if double check doesn't have exactly two check types.
        """
        super(KriegspielAnswer, self).__init__()
        # Validation, that main announcement, can be only
        # Main Announcement.
        if not isinstance(main_announcement, MainAnnouncement):
            raise TypeError("main_announcement must be a MainAnnouncement")

        self._main_announcement = main_announcement
        self._capture_at_square = None
        self._captured_piece_announcement = None
        self._special_announcement = SpecialCaseAnnouncement.NONE
        self._move_done = False
        self._check_1 = None
        self._check_2 = None
        self._next_turn_pawn_tries = None
        self._next_turn_has_pawn_capture = None

        if main_announcement == MainAnnouncement.CAPTURE_DONE:
            # Validation, that when capture is done, then valid square should
            # announced. Chess lib store squares as ints.
            if not isinstance(kwargs.get("capture_at_square"), int):
                raise TypeError("Capture square must be an integer")
            square = kwargs["capture_at_square"]
            if not (0 <= square <= 63):  # Chess board has 64 squares (0-63)
                raise ValueError(f"Invalid square number: {square}. Must be 0-63.")
            self._capture_at_square = square
            if "captured_piece_announcement" in kwargs:
                captured_piece_announcement = kwargs["captured_piece_announcement"]
                if not isinstance(captured_piece_announcement, CapturedPieceAnnouncement):
                    raise TypeError("captured_piece_announcement must be a CapturedPieceAnnouncement")
                self._captured_piece_announcement = captured_piece_announcement
        elif "captured_piece_announcement" in kwargs:
            raise TypeError("captured_piece_announcement is only valid for CAPTURE_DONE")

        if "special_announcement" in kwargs:
            sca = kwargs["special_announcement"]
            if isinstance(sca, SpecialCaseAnnouncement):
                self._special_announcement = sca
            elif isinstance(sca, tuple):
                if sca[0] == SpecialCaseAnnouncement.CHECK_DOUBLE:
                    self._special_announcement = SpecialCaseAnnouncement.CHECK_DOUBLE
                    # Validation that double check has exactly two checks
                    if not isinstance(sca[1], (list, tuple)) or len(sca[1]) != 2:
                        raise ValueError("Double check must have exactly two check types")
                    for check in sca[1]:
                        # Validation, that both checks correspond to double check
                        # are single check.
                        if not check in SINGLE_CHECK:
                            raise TypeError("Each check in double check must be a valid single check type")
                    self._check_1 = sca[1][0]
                    self._check_2 = sca[1][1]
                else:
                    # Validation, that if it's tuple, then only double check
                    # is the option.
                    raise TypeError("Tuple special announcements are only valid for CHECK_DOUBLE")
            else:
                # Validation, that Special Case Announcement could be SCA or tuple.
                raise TypeError(
                    "special_announcement must be a SpecialCaseAnnouncement or a CHECK_DOUBLE tuple"
                )

        if "next_turn_pawn_tries" in kwargs:
            next_turn_pawn_tries = kwargs["next_turn_pawn_tries"]
            if not isinstance(next_turn_pawn_tries, int):
                raise TypeError("next_turn_pawn_tries must be an integer")
            if next_turn_pawn_tries < 0:
                raise ValueError("next_turn_pawn_tries must be non-negative")
            self._next_turn_pawn_tries = next_turn_pawn_tries

        if "next_turn_has_pawn_capture" in kwargs:
            next_turn_has_pawn_capture = kwargs["next_turn_has_pawn_capture"]
            if not isinstance(next_turn_has_pawn_capture, bool):
                raise TypeError("next_turn_has_pawn_capture must be a boolean")
            self._next_turn_has_pawn_capture = next_turn_has_pawn_capture

        if self._next_turn_pawn_tries is not None and self._next_turn_has_pawn_capture is not None:
            raise ValueError("Use either next_turn_pawn_tries or next_turn_has_pawn_capture, not both")

        if self._main_announcement in MOVE_DONE:
            self._move_done = True

    @property
    def main_announcement(self):
        """
        Get the primary outcome of the move question.
        
        Returns:
            MainAnnouncement: The main response type (MOVE_DONE, CAPTURE_DONE, etc.)
        """
        return self._main_announcement

    @property
    def capture_at_square(self):
        """
        Get the square where a capture occurred.
        
        Returns:
            int or None: Square number (0-63) if a capture happened, None otherwise.
                        Only set when main_announcement is CAPTURE_DONE.
        """
        return self._capture_at_square

    @property
    def special_announcement(self):
        """
        Get any special game state announcement.
        
        Returns:
            SpecialCaseAnnouncement: Special condition like CHECK_RANK, CHECKMATE_WHITE_WINS,
                                   DRAW_STALEMATE, etc. Returns NONE if no special condition.
        """
        return self._special_announcement

    @property
    def captured_piece_announcement(self):
        """
        Get the public capture kind for variants that expose pawn vs piece.

        Returns:
            CapturedPieceAnnouncement or None: Public capture kind when available.
        """
        return self._captured_piece_announcement

    @property
    def move_done(self):
        """
        Check if the move was successfully completed.
        
        Returns:
            bool: True if the move was executed (MOVE_DONE or CAPTURE_DONE),
                 False if move was illegal or impossible.
        """
        return self._move_done

    @property
    def next_turn_pawn_tries(self):
        """
        Get the next player's legal pawn-capture count when the ruleset announces it.

        Returns:
            int or None: Wild 16 style pawn-try count for the next player to move.
        """
        return self._next_turn_pawn_tries

    @property
    def next_turn_has_pawn_capture(self):
        """
        Get the next player's binary pawn-capture announcement when the ruleset exposes it.

        Returns:
            bool or None: Cincinnati-style pawn-capture availability for the next player.
        """
        return self._next_turn_has_pawn_capture

    @property
    def check_1(self):
        """
        Get the first check type in a double check situation.
        
        Returns:
            SpecialCaseAnnouncement or None: First check type when special_announcement
                                            is CHECK_DOUBLE, None otherwise.
        """
        return self._check_1

    @property
    def check_2(self):
        """
        Get the second check type in a double check situation.
        
        Returns:
            SpecialCaseAnnouncement or None: Second check type when special_announcement
                                            is CHECK_DOUBLE, None otherwise.
        """
        return self._check_2

    def __str__(self):
        """
        Return string representation of the answer.
        
        Returns:
            String showing main announcement, capture square (if any), special cases,
            and check details in format "<KriegspielAnswer: main_announcement, details>"
        """
        capture_at = None
        if isinstance(self._capture_at_square, int):
            capture_at = chess.SQUARE_NAMES[self._capture_at_square]

        main_data = [
            f"capture_at={capture_at}",
            f"captured_piece={self._captured_piece_announcement}",
            f"special_case={self._special_announcement}",
            f"next_turn_pawn_tries={self._next_turn_pawn_tries}",
        ]
        if self._next_turn_has_pawn_capture is not None:
            main_data.append(f"next_turn_has_pawn_capture={self._next_turn_has_pawn_capture}")

        if self._check_1 is not None or self._check_2 is not None:
            extra_data = f"check_1={self._check_1}, check_2={self._check_2}"
            main_data.append(extra_data)

        return f'<KriegspielAnswer: {self._main_announcement}, {", ".join(main_data)}>'

    def _identity_key(self):
        return (
            self._main_announcement,
            self._capture_at_square,
            self._captured_piece_announcement,
            self._special_announcement,
            self._next_turn_pawn_tries,
            self._next_turn_has_pawn_capture,
            self._check_1,
            self._check_2,
        )

    def _sort_key(self):
        return (
            self._main_announcement.value,
            self._capture_at_square,
            self._captured_piece_announcement.value if self._captured_piece_announcement is not None else -1,
            self._special_announcement.value,
            self._next_turn_pawn_tries if self._next_turn_pawn_tries is not None else -1,
            -1 if self._next_turn_has_pawn_capture is None else int(self._next_turn_has_pawn_capture),
            self._check_1.value if self._check_1 is not None else -1,
            self._check_2.value if self._check_2 is not None else -1,
        )

    def __repr__(self):
        """
        Return detailed string representation of the answer.
        
        Returns:
            Same as __str__ for debugging purposes.
        """
        return self.__str__()

    def __eq__(self, other):
        """
        Check equality with another KriegspielAnswer.
        
        Two answers are equal if their string representations match.
        
        Args:
            other: Object to compare with.
            
        Returns:
            True if answers are equivalent, False otherwise.
        """
        if not isinstance(other, KriegspielAnswer):
            return NotImplemented
        return self._identity_key() == other._identity_key()

    def __ne__(self, other):
        """
        Check inequality with another KriegspielAnswer.
        
        Args:
            other: Object to compare with.
            
        Returns:
            True if answers are not equivalent, False if they are equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __lt__(self, other):
        """
        Compare answers for sorting purposes.
        
        Comparison is based on structured answer identity for stable ordering.
        
        Args:
            other: Another KriegspielAnswer to compare with.
            
        Returns:
            True if this answer should be sorted before the other.
        """
        if not isinstance(other, KriegspielAnswer):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __hash__(self):
        """
        Generate hash value for the answer.
        
        Enables KriegspielAnswer objects to be used in sets and as dictionary keys.
        Hash is based on the same structured identity used for equality.
        
        Returns:
            Integer hash value.
        """
        return hash(self._identity_key())


class KriegspielScoresheet:
    """
    Maintains game history for a player in Kriegspiel.
    
    This class tracks both the player's own moves and the opponent's visible moves
    with their outcomes, enabling game replay and analysis. Each player has their
    own scoresheet containing only the information visible to them.
    """
    
    def __init__(self, color=chess.WHITE):
        """
        Initialize a scoresheet for a player.
        
        Args:
            color: Chess color (chess.WHITE or chess.BLACK) of the player
                  this scoresheet belongs to. Defaults to WHITE.
        """
        self.__color = color
        self.__moves_own = []
        self.__moves_opponent = []
        self.__last_move_number = 0

    @property
    def moves_own(self):
        """
        Get the player's own move history.
        
        Returns:
            List of move sets, where each move set is a list of (question, answer) pairs
            representing all questions asked during one turn.
        """
        return self.__moves_own

    @property
    def moves_opponent(self):
        """
        Get the opponent's visible move history.
        
        Returns:
            List of move sets, where each move set contains the opponent's questions
            and answers that were visible to this player.
        """
        return self.__moves_opponent

    @property
    def last_move_number(self):
        """Expose the current internal move-number cursor for snapshots."""
        return self.__last_move_number

    @property
    def color(self):
        """
        Get the color of the player this scoresheet belongs to.
        
        Returns:
            bool: chess.WHITE (True) or chess.BLACK (False)
        """
        return self.__color

    def was_the_last_move_ended(self, color):
        """
        Check if the last move by the specified color resulted in a completed move.
        
        Args:
            color: Chess color (chess.WHITE or chess.BLACK) to check
            
        Returns:
            bool: True if the last move was completed (not just a question),
                 False if the last question was illegal or impossible.
        """
        if self.__color == color:
            last_set_of_questions = self.__moves_own[-1]
        else:
            last_set_of_questions = self.__moves_opponent[-1]
        last_pair = last_set_of_questions[-1]
        last_answer = last_pair[1]
        return last_answer.move_done

    def __get_current_move_number(self):
        """
        Get the current move number for recording purposes.
        
        Private method that tracks move numbering to organize questions
        and answers into proper turn sequences.
        
        Returns:
            int: Current move number for organizing the scoresheet.
        """
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
        """
        Record a move made by this player.
        
        Args:
            move: KriegspielMove object representing the question asked
            answer: KriegspielAnswer object representing the referee's response
            
        Raises:
            ValueError: If move is not a KriegspielMove or answer is not a KriegspielAnswer
        """
        if not isinstance(move, KriegspielMove):
            raise ValueError("move must be a KriegspielMove")
        if not isinstance(answer, KriegspielAnswer):
            raise ValueError("answer must be a KriegspielAnswer")
        current_move_number = self.__get_current_move_number()
        if current_move_number == len(self.__moves_own):
            self.__moves_own[-1].append((move, answer))
        else:
            self.__moves_own.append([(move, answer)])

    def record_move_opponent(self, question, answer):
        """
        Record a move made by the opponent that was visible to this player.
        
        Args:
            question: QuestionAnnouncement representing the type of opponent's question
            answer: KriegspielAnswer object representing the referee's response
                   that was announced to this player
            
        Raises:
            ValueError: If question is not a QuestionAnnouncement or answer is not a KriegspielAnswer
        """
        if not isinstance(question, QuestionAnnouncement):
            raise ValueError("question must be a QuestionAnnouncement")
        if not isinstance(answer, KriegspielAnswer):
            raise ValueError("answer must be a KriegspielAnswer")
        current_move_number = self.__get_current_move_number()
        if current_move_number == len(self.__moves_opponent):
            self.__moves_opponent[-1].append((question, answer))
        else:
            self.__moves_opponent.append([(question, answer)])

    def snapshot(self):
        """Return a public, serialization-friendly snapshot of this scoresheet."""
        from kriegspiel.snapshot import ScoresheetSnapshot

        return ScoresheetSnapshot(
            color=self.__color,
            moves_own=tuple(tuple(turn) for turn in self.__moves_own),
            moves_opponent=tuple(tuple(turn) for turn in self.__moves_opponent),
            last_move_number=self.__last_move_number,
        )

    @classmethod
    def from_snapshot(cls, snapshot):
        """Build a scoresheet from a public snapshot."""
        from kriegspiel.snapshot import ScoresheetSnapshot

        if not isinstance(snapshot, ScoresheetSnapshot):
            raise TypeError("snapshot must be a ScoresheetSnapshot")

        scoresheet = cls(snapshot.color)
        scoresheet.__moves_own = [list(turn) for turn in snapshot.moves_own]
        scoresheet.__moves_opponent = [list(turn) for turn in snapshot.moves_opponent]
        scoresheet.__last_move_number = snapshot.last_move_number
        return scoresheet
