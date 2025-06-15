# -*- coding: utf-8 -*-

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from kriegspiel.berkeley import chess, BerkeleyGame
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA
from kriegspiel.move import KriegspielAnswer as KSAnswer
from kriegspiel.move import MainAnnouncement as MA
from kriegspiel.move import SpecialCaseAnnouncement as SCA


# Custom strategies for chess-related data
@composite
def valid_square(draw):
    """Generate a valid chess square (0-63)."""
    return draw(st.integers(min_value=0, max_value=63))


@composite
def chess_move(draw):
    """Generate a valid chess.Move object."""
    from_square = draw(valid_square())
    to_square = draw(valid_square())
    # Only add promotion if it's a potential pawn promotion move
    promotion = None
    if (from_square // 8 == 6 and to_square // 8 == 7) or (from_square // 8 == 1 and to_square // 8 == 0):
        promotion = draw(st.sampled_from([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]))
    return chess.Move(from_square, to_square, promotion=promotion)


@composite
def kriegspiel_move(draw):
    """Generate a KriegspielMove."""
    question_type = draw(st.sampled_from([QA.COMMON, QA.ASK_ANY]))
    if question_type == QA.ASK_ANY:
        return KSMove(QA.ASK_ANY)
    else:
        move = draw(chess_move())
        return KSMove(QA.COMMON, move)


# Property-based tests
@pytest.mark.property
class TestGameInvariants:
    """Test invariants that should hold for all game states."""

    @given(valid_square(), valid_square())
    @settings(max_examples=50)
    def test_move_from_empty_square_always_impossible(self, from_sq, to_sq):
        """Any move from an empty square should be impossible to ask."""
        assume(from_sq != to_sq)  # Skip null moves
        
        g = BerkeleyGame()
        g._board.clear()  # Empty board
        g._generate_possible_to_ask_list()
        
        move = KSMove(QA.COMMON, chess.Move(from_sq, to_sq))
        result = g.ask_for(move)
        assert result.main_announcement == MA.IMPOSSIBLE_TO_ASK

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_ask_any_multiple_times_after_first_impossible(self, num_asks):
        """After asking ANY once, subsequent ANY questions should be impossible."""
        g = BerkeleyGame()
        
        # First ASK_ANY should work
        first_result = g.ask_for(KSMove(QA.ASK_ANY))
        assert first_result.main_announcement in [MA.HAS_ANY, MA.NO_ANY]
        
        # All subsequent ASK_ANY should be impossible
        for _ in range(num_asks):
            result = g.ask_for(KSMove(QA.ASK_ANY))
            assert result.main_announcement == MA.IMPOSSIBLE_TO_ASK

    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=10)
    def test_game_over_means_no_possible_moves(self, moves_to_try):
        """When game is over, no moves should be possible."""
        # Create a checkmate position
        g = BerkeleyGame()
        g._board.clear()
        g._board.set_piece_at(chess.C2, chess.Piece(chess.KING, chess.WHITE))
        g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
        g._board.set_piece_at(chess.G1, chess.Piece(chess.ROOK, chess.WHITE))
        g._board.set_piece_at(chess.B7, chess.Piece(chess.QUEEN, chess.WHITE))
        g._board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
        g._generate_possible_to_ask_list()
        
        # Execute checkmate
        g.ask_for(KSMove(QA.COMMON, chess.Move(chess.A1, chess.A8)))
        
        # Game should be over
        assert g.game_over
        
        # Try random moves - all should be impossible
        for _ in range(moves_to_try):
            move = KSMove(QA.COMMON, chess.Move(chess.A1, chess.A2))
            result = g.ask_for(move)
            assert result.main_announcement == MA.IMPOSSIBLE_TO_ASK

    @given(st.integers(min_value=0, max_value=63))
    @settings(max_examples=20)
    def test_capture_always_reports_capture_square(self, capture_square):
        """When a capture occurs, the capture square should always be reported."""
        g = BerkeleyGame()
        g._board.clear()
        
        # Set up a simple capture scenario
        g._board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
        g._board.set_piece_at(capture_square, chess.Piece(chess.PAWN, chess.BLACK))
        g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
        g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
        g._generate_possible_to_ask_list()
        
        # If the capture is possible, it should report the square
        move = KSMove(QA.COMMON, chess.Move(chess.E4, capture_square))
        if move in g.possible_to_ask:
            result = g.ask_for(move)
            if result.main_announcement == MA.CAPTURE_DONE:
                assert result.capture_at_square == capture_square


@pytest.mark.property
class TestMoveGeneration:
    """Test properties of move generation."""

    def test_initial_position_has_expected_move_count(self):
        """Initial position should have exactly 35 possible moves."""
        g = BerkeleyGame()
        assert len(g.possible_to_ask) == 35

    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=10)
    def test_possible_moves_list_consistency(self, random_seed):
        """The possible moves list should be consistent across regenerations."""
        g = BerkeleyGame()
        
        # Get initial possible moves
        initial_moves = set(g.possible_to_ask)
        
        # Regenerate and check consistency
        g._generate_possible_to_ask_list()
        regenerated_moves = set(g.possible_to_ask)
        
        assert initial_moves == regenerated_moves

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=10)
    def test_ask_any_always_possible_until_used(self, num_other_moves):
        """ASK_ANY should always be in possible moves until it's used."""
        g = BerkeleyGame()
        
        # ASK_ANY should be possible initially
        assert KSMove(QA.ASK_ANY) in g.possible_to_ask
        
        # Make some regular moves
        moves_made = 0
        for move in list(g.possible_to_ask):
            if move.question_type == QA.COMMON and moves_made < min(num_other_moves, 5):
                result = g.ask_for(move)
                if result.main_announcement in [MA.REGULAR_MOVE, MA.CAPTURE_DONE]:
                    moves_made += 1
                    # ASK_ANY should still be possible
                    assert KSMove(QA.ASK_ANY) in g.possible_to_ask
                if moves_made >= 5:  # Limit to prevent infinite loops
                    break


@pytest.mark.property
class TestAnswerProperties:
    """Test properties of KriegspielAnswer objects."""

    @given(st.sampled_from([MA.REGULAR_MOVE, MA.ILLEGAL_MOVE, MA.IMPOSSIBLE_TO_ASK]))
    def test_answer_equality_and_hashing(self, main_announcement):
        """Answers with same content should be equal and have same hash."""
        answer1 = KSAnswer(main_announcement)
        answer2 = KSAnswer(main_announcement)
        
        assert answer1 == answer2
        assert hash(answer1) == hash(answer2)

    @given(st.sampled_from([SCA.CHECK_RANK, SCA.CHECK_FILE, SCA.CHECK_KNIGHT]))
    def test_special_announcements_preserved(self, special_announcement):
        """Special announcements should be preserved in answers."""
        answer = KSAnswer(MA.REGULAR_MOVE, special_announcement=special_announcement)
        assert answer.special_announcement == special_announcement

    @given(valid_square())
    def test_capture_square_preserved(self, square):
        """Capture squares should be preserved in answers."""
        answer = KSAnswer(MA.CAPTURE_DONE, capture_at_square=square)
        assert answer.capture_at_square == square


if __name__ == "__main__":
    pytest.main([__file__])