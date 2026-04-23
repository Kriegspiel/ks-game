#!/usr/bin/env python3
"""Micro-benchmark helper for Berkeley move-generation scenarios."""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import chess

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kriegspiel.berkeley import BerkeleyGame
from kriegspiel.move import KriegspielMove as KSMove
from kriegspiel.move import QuestionAnnouncement as QA


def build_initial() -> BerkeleyGame:
    return BerkeleyGame()


def build_midgame() -> BerkeleyGame:
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


def build_hidden_blocker() -> BerkeleyGame:
    game = BerkeleyGame(any_rule=False)
    game._board.clear()
    game._board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    game._board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    game._board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    game._board.set_piece_at(chess.D2, chess.Piece(chess.KNIGHT, chess.BLACK))
    game._generate_possible_to_ask_list()
    return game


def build_long_game() -> BerkeleyGame:
    game = BerkeleyGame()
    for _ in range(40):
        game.ask_for(KSMove(QA.COMMON, chess.Move(chess.G1, chess.F3)))
        game.ask_for(KSMove(QA.COMMON, chess.Move(chess.G8, chess.F6)))
        game.ask_for(KSMove(QA.COMMON, chess.Move(chess.F3, chess.G1)))
        game.ask_for(KSMove(QA.COMMON, chess.Move(chess.F6, chess.G8)))
    return game


SCENARIOS = {
    "initial": build_initial,
    "midgame": build_midgame,
    "hidden-blocker": build_hidden_blocker,
    "long-game": build_long_game,
}


def benchmark(game: BerkeleyGame, iterations: int, rounds: int) -> tuple[list[float], int]:
    run_times = []
    askable_count = len(game.possible_to_ask)
    for _ in range(rounds):
        start = time.perf_counter()
        for _ in range(iterations):
            game._generate_possible_to_ask_list()
        elapsed = time.perf_counter() - start
        run_times.append(elapsed)
        askable_count = len(game.possible_to_ask)
    return run_times, askable_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark BerkeleyGame move generation")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="initial")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()

    game = SCENARIOS[args.scenario]()
    run_times, askable_count = benchmark(game, args.iterations, args.rounds)

    mean_seconds = statistics.mean(run_times)
    median_seconds = statistics.median(run_times)
    per_call_us = (mean_seconds / args.iterations) * 1_000_000

    print(f"scenario={args.scenario}")
    print(f"iterations={args.iterations}")
    print(f"rounds={args.rounds}")
    print(f"askable_count={askable_count}")
    print(f"mean_seconds={mean_seconds:.6f}")
    print(f"median_seconds={median_seconds:.6f}")
    print(f"mean_microseconds_per_call={per_call_us:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
