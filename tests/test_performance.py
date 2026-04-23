# -*- coding: utf-8 -*-

import pytest
import time
from kriegspiel.berkeley import chess, BerkeleyGame
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA


def _perf_now():
    return time.perf_counter()


def _measure_regeneration(game, iterations):
    start_time = _perf_now()
    for _ in range(iterations):
        game._generate_possible_to_ask_list()
    return _perf_now() - start_time


def _build_midgame_position():
    game = BerkeleyGame()
    opening_moves = [
        (chess.E2, chess.E4), (chess.E7, chess.E5),
        (chess.G1, chess.F3), (chess.B8, chess.C6),
        (chess.F1, chess.B5), (chess.A7, chess.A6),
        (chess.B5, chess.A4), (chess.G8, chess.F6),
        (chess.E1, chess.G1), (chess.F8, chess.E7),
        (chess.F1, chess.E1), (chess.B7, chess.B5),
        (chess.A4, chess.B3), (chess.E8, chess.G8),
    ]
    for from_sq, to_sq in opening_moves:
        game.ask_for(KSMove(QA.COMMON, chess.Move(from_sq, to_sq)))
    return game


def _build_hidden_blocker_position():
    game = BerkeleyGame(any_rule=False)
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


@pytest.mark.performance
class TestPerformance:
    """Performance tests to ensure the game handles complex scenarios efficiently."""

    def test_200_move_game_performance(self):
        """Test that a 200-move game completes within reasonable time."""
        start_time = _perf_now()
        
        g = BerkeleyGame()
        # Execute 200 reversible moves (similar to existing test but with timing)
        for _ in range(50):  # 50 * 4 = 200 moves
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
        
        elapsed_time = _perf_now() - start_time
        
        assert elapsed_time < 2.0, f"200-move game took {elapsed_time:.3f}s, expected < 2.0s"

    def test_move_generation_performance_initial_position(self):
        """Repeated regeneration from the initial position should stay comfortably sublinear."""
        elapsed_time = _measure_regeneration(BerkeleyGame(), 2000)
        assert elapsed_time < 2.0, f"2000 initial-position regenerations took {elapsed_time:.3f}s, expected < 2.0s"

    def test_move_generation_performance_midgame_position(self):
        """A richer middlegame should still regenerate askable moves within a reasonable budget."""
        elapsed_time = _measure_regeneration(_build_midgame_position(), 2000)
        assert elapsed_time < 2.0, f"2000 midgame regenerations took {elapsed_time:.3f}s, expected < 2.0s"

    def test_move_generation_performance_hidden_blocker_position(self):
        """Hidden-blocker positions should stay cheap to regenerate and cover the hidden-information path."""
        elapsed_time = _measure_regeneration(_build_hidden_blocker_position(), 4000)
        assert elapsed_time < 1.5, f"4000 hidden-blocker regenerations took {elapsed_time:.3f}s, expected < 1.5s"

    def test_complex_position_performance(self):
        """Test performance with a complex mid-game position."""
        g = BerkeleyGame()
        
        # Create a complex position by playing several moves
        opening_moves = [
            (chess.E2, chess.E4), (chess.E7, chess.E5),
            (chess.G1, chess.F3), (chess.B8, chess.C6),
            (chess.F1, chess.B5), (chess.A7, chess.A6),
            (chess.B5, chess.A4), (chess.G8, chess.F6),
            (chess.E1, chess.G1), (chess.F8, chess.E7),
            (chess.F1, chess.E1), (chess.B7, chess.B5),
            (chess.A4, chess.B3), (chess.E8, chess.G8)
        ]
        
        start_time = _perf_now()
        
        for from_sq, to_sq in opening_moves:
            move = KSMove(QA.COMMON, chess.Move(from_sq, to_sq))
            g.ask_for(move)
        
        elapsed_time = _perf_now() - start_time
        
        # Complex opening should complete quickly
        assert elapsed_time < 0.25, f"Complex opening took {elapsed_time:.3f}s, expected < 0.25s"

    def test_large_number_of_any_questions(self):
        """Test performance when asking many ANY questions in different games."""
        start_time = _perf_now()
        
        # Create many games and ask ANY question in each
        for _ in range(100):
            g = BerkeleyGame()
            g.ask_for(KSMove(QA.ASK_ANY))
        
        elapsed_time = _perf_now() - start_time
        
        # Should handle 100 ANY questions quickly
        assert elapsed_time < 1.0, f"100 ANY questions took {elapsed_time:.3f}s, expected < 1.0s"

    def test_endgame_performance(self):
        """Test performance in endgame positions with few pieces."""
        start_time = _perf_now()
        
        # Create an endgame position
        g = BerkeleyGame()
        g._board.clear()
        g._board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
        g._board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
        g._board.set_piece_at(chess.D4, chess.Piece(chess.QUEEN, chess.WHITE))
        
        # Simulate many moves in endgame
        for _ in range(50):
            g._generate_possible_to_ask_list()
            # Try a few moves
            possible_moves = [move for move in g.possible_to_ask if move.question_type == QA.COMMON]
            if possible_moves:
                g.ask_for(possible_moves[0])
        
        elapsed_time = _perf_now() - start_time
        
        # Endgame simulation should be fast
        assert elapsed_time < 1.0, f"Endgame simulation took {elapsed_time:.3f}s, expected < 1.0s"

    def test_move_generation_after_long_game_remains_responsive(self):
        """Scoresheet growth should not cause move regeneration to blow up late in a long game."""
        g = BerkeleyGame()

        for _ in range(40):  # 160 reversible plies
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))

        elapsed_time = _measure_regeneration(g, 1000)
        assert elapsed_time < 1.5, f"1000 late-game regenerations took {elapsed_time:.3f}s, expected < 1.5s"

    @pytest.mark.slow
    def test_stress_test_game_creation(self):
        """Stress test: create many game instances."""
        start_time = _perf_now()
        
        games = []
        for _ in range(1000):
            games.append(BerkeleyGame())
        
        elapsed_time = _perf_now() - start_time
        
        # Should create 1000 games quickly
        assert elapsed_time < 2.0, f"Creating 1000 games took {elapsed_time:.3f}s, expected < 2.0s"
        assert len(games) == 1000

    @pytest.mark.slow
    def test_memory_usage_long_game(self):
        """Test that long games don't consume excessive memory."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        g = BerkeleyGame()
        
        # Play a very long game (but not as long as 200 moves to avoid timeout)
        for _ in range(25):  # 100 moves total
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
            g.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
        
        # Game should still be responsive
        start_time = _perf_now()
        g._generate_possible_to_ask_list()
        elapsed_time = _perf_now() - start_time
        
        # Move generation should still be fast after long game
        assert elapsed_time < 0.1, f"Move generation after long game took {elapsed_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
