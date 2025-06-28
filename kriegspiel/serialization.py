# -*- coding: utf-8 -*-

"""
JSON serialization support for Kriegspiel game state.

This module provides comprehensive serialization and deserialization for all
Kriegspiel game components using JSON format with custom encoders/decoders.

JSON Schema Structure:
{
  "version": "1.2.0",
  "game_type": "BerkeleyGame",
  "game_state": {
    "any_rule": bool,
    "board_fen": str,
    "must_use_pawns": bool, 
    "game_over": bool,
    "white_scoresheet": {
      "color": "WHITE",
      "moves_own": [...],
      "moves_opponent": [...],
      "last_move_number": int
    },
    "black_scoresheet": {
      "color": "BLACK", 
      "moves_own": [...],
      "moves_opponent": [...],
      "last_move_number": int
    }
  }
}

Move History Structure:
moves_own/moves_opponent: [
  [  // Move set (one turn)
    [  // Question-Answer pair
      {  // KriegspielMove
        "question_type": "COMMON" | "ASK_ANY",
        "chess_move": "e2e4" | null  // UCI notation
      },
      {  // KriegspielAnswer
        "main_announcement": "REGULAR_MOVE" | "CAPTURE_DONE" | ...,
        "capture_at_square": int | null,
        "special_announcement": "NONE" | "CHECK_RANK" | ...,
        "check_1": "CHECK_RANK" | null,  // For double check
        "check_2": "CHECK_FILE" | null   // For double check
      }
    ]
  ]
]
"""

import json
import chess
from typing import Dict, Any, List, Tuple, Union, Optional

from kriegspiel.move import (
    QuestionAnnouncement, MainAnnouncement, SpecialCaseAnnouncement,
    KriegspielMove, KriegspielAnswer, KriegspielScoresheet
)

# Import version from main module
from kriegspiel import __version__

# Current serialization format version matches module version
SERIALIZATION_VERSION = __version__


class SerializationError(Exception):
    """Base exception for serialization errors."""
    pass


class UnsupportedVersionError(SerializationError):
    """Raised when trying to load a game with unsupported version."""
    pass


class MalformedDataError(SerializationError):
    """Raised when trying to deserialize malformed or invalid data."""
    pass


class KriegspielJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Kriegspiel game objects."""
    
    def default(self, obj):
        """Convert Kriegspiel objects to JSON-serializable format."""
        if isinstance(obj, chess.Move):
            return obj.uci()
        elif isinstance(obj, (QuestionAnnouncement, MainAnnouncement, SpecialCaseAnnouncement)):
            return obj.name
        elif isinstance(obj, KriegspielMove):
            return serialize_kriegspiel_move(obj)
        elif isinstance(obj, KriegspielAnswer):
            return serialize_kriegspiel_answer(obj)
        elif isinstance(obj, KriegspielScoresheet):
            return serialize_kriegspiel_scoresheet(obj)
        elif obj.__class__.__name__ == 'BerkeleyGame':
            return serialize_berkeley_game(obj)
        else:
            return super().default(obj)


def serialize_chess_move(move: Optional[chess.Move]) -> Optional[str]:
    """Serialize chess.Move to UCI notation string."""
    return move.uci() if move is not None else None


def deserialize_chess_move(uci_str: Optional[str]) -> Optional[chess.Move]:
    """Deserialize UCI notation string to chess.Move."""
    if uci_str is None:
        return None
    try:
        return chess.Move.from_uci(uci_str)
    except ValueError as e:
        raise MalformedDataError(f"Invalid UCI move string: {uci_str}") from e


def serialize_enum(enum_val: Union[QuestionAnnouncement, MainAnnouncement, SpecialCaseAnnouncement]) -> str:
    """Serialize enum to its name string."""
    return enum_val.name


def deserialize_question_announcement(name: str) -> QuestionAnnouncement:
    """Deserialize string name to QuestionAnnouncement enum."""
    try:
        return QuestionAnnouncement[name]
    except KeyError as e:
        raise MalformedDataError(f"Invalid QuestionAnnouncement: {name}") from e


def deserialize_main_announcement(name: str) -> MainAnnouncement:
    """Deserialize string name to MainAnnouncement enum."""
    try:
        return MainAnnouncement[name]
    except KeyError as e:
        raise MalformedDataError(f"Invalid MainAnnouncement: {name}") from e


def deserialize_special_case_announcement(name: str) -> SpecialCaseAnnouncement:
    """Deserialize string name to SpecialCaseAnnouncement enum."""
    try:
        return SpecialCaseAnnouncement[name]
    except KeyError as e:
        raise MalformedDataError(f"Invalid SpecialCaseAnnouncement: {name}") from e


def serialize_kriegspiel_move(move: KriegspielMove) -> Dict[str, Any]:
    """Serialize KriegspielMove to dictionary."""
    return {
        "question_type": serialize_enum(move.question_type),
        "chess_move": serialize_chess_move(move.chess_move)
    }


def deserialize_kriegspiel_move(data: Dict[str, Any]) -> KriegspielMove:
    """Deserialize dictionary to KriegspielMove."""
    try:
        question_type = deserialize_question_announcement(data["question_type"])
        chess_move = deserialize_chess_move(data["chess_move"])
        return KriegspielMove(question_type, chess_move)
    except (KeyError, TypeError) as e:
        raise MalformedDataError(f"Invalid KriegspielMove data: {data}") from e


def serialize_kriegspiel_answer(answer: KriegspielAnswer) -> Dict[str, Any]:
    """Serialize KriegspielAnswer to dictionary."""
    return {
        "main_announcement": serialize_enum(answer.main_announcement),
        "capture_at_square": answer.capture_at_square,
        "special_announcement": serialize_enum(answer.special_announcement),
        "check_1": serialize_enum(answer.check_1) if answer.check_1 is not None else None,
        "check_2": serialize_enum(answer.check_2) if answer.check_2 is not None else None
    }


def deserialize_kriegspiel_answer(data: Dict[str, Any]) -> KriegspielAnswer:
    """Deserialize dictionary to KriegspielAnswer."""
    try:
        main_announcement = deserialize_main_announcement(data["main_announcement"])
        
        # Build kwargs for KriegspielAnswer constructor
        kwargs = {}
        
        if data.get("capture_at_square") is not None:
            kwargs["capture_at_square"] = data["capture_at_square"]
        
        special_announcement = deserialize_special_case_announcement(data["special_announcement"])
        
        # Handle double check case
        if (special_announcement == SpecialCaseAnnouncement.CHECK_DOUBLE and 
            data.get("check_1") is not None and data.get("check_2") is not None):
            check_1 = deserialize_special_case_announcement(data["check_1"])
            check_2 = deserialize_special_case_announcement(data["check_2"])
            kwargs["special_announcement"] = (SpecialCaseAnnouncement.CHECK_DOUBLE, [check_1, check_2])
        elif special_announcement != SpecialCaseAnnouncement.NONE:
            kwargs["special_announcement"] = special_announcement
        
        return KriegspielAnswer(main_announcement, **kwargs)
    except (KeyError, TypeError, ValueError) as e:
        raise MalformedDataError(f"Invalid KriegspielAnswer data: {data}") from e


def serialize_kriegspiel_scoresheet(scoresheet: KriegspielScoresheet) -> Dict[str, Any]:
    """Serialize KriegspielScoresheet to dictionary."""
    return {
        "color": "WHITE" if scoresheet.color == chess.WHITE else "BLACK",
        "moves_own": [
            [(serialize_kriegspiel_move(move), serialize_kriegspiel_answer(answer)) 
             for move, answer in move_set]
            for move_set in scoresheet.moves_own
        ],
        "moves_opponent": [
            [(serialize_enum(question), serialize_kriegspiel_answer(answer))
             for question, answer in move_set]
            for move_set in scoresheet.moves_opponent
        ],
        "last_move_number": scoresheet._KriegspielScoresheet__last_move_number
    }


def deserialize_kriegspiel_scoresheet(data: Dict[str, Any]) -> KriegspielScoresheet:
    """Deserialize dictionary to KriegspielScoresheet."""
    try:
        color = chess.WHITE if data["color"] == "WHITE" else chess.BLACK
        scoresheet = KriegspielScoresheet(color)
        
        # Restore move history
        scoresheet._KriegspielScoresheet__moves_own = [
            [(deserialize_kriegspiel_move(move_data), deserialize_kriegspiel_answer(answer_data))
             for move_data, answer_data in move_set]
            for move_set in data["moves_own"]
        ]
        
        scoresheet._KriegspielScoresheet__moves_opponent = [
            [(deserialize_question_announcement(question_data), deserialize_kriegspiel_answer(answer_data))
             for question_data, answer_data in move_set]
            for move_set in data["moves_opponent"]
        ]
        
        scoresheet._KriegspielScoresheet__last_move_number = data["last_move_number"]
        
        return scoresheet
    except (KeyError, TypeError, ValueError) as e:
        raise MalformedDataError(f"Invalid KriegspielScoresheet data") from e


def serialize_berkeley_game(game) -> Dict[str, Any]:
    """Serialize BerkeleyGame to dictionary."""
    return {
        "version": SERIALIZATION_VERSION,
        "game_type": "BerkeleyGame",
        "game_state": {
            "any_rule": game._any_rule,
            "board_fen": game._board.fen(),
            "must_use_pawns": game._must_use_pawns,
            "game_over": game._game_over,
            "white_scoresheet": serialize_kriegspiel_scoresheet(game._whites_scoresheet),
            "black_scoresheet": serialize_kriegspiel_scoresheet(game._blacks_scoresheet)
        }
    }


def deserialize_berkeley_game(data: Dict[str, Any]):
    """Deserialize dictionary to BerkeleyGame."""
    try:
        # Check version compatibility
        version = data.get("version", "unknown")
        if version != SERIALIZATION_VERSION:
            raise UnsupportedVersionError(f"Unsupported version: {version}. Expected: {SERIALIZATION_VERSION}")
        
        # Check game type
        game_type = data.get("game_type", "unknown")
        if game_type != "BerkeleyGame":
            raise MalformedDataError(f"Invalid game type: {game_type}. Expected: BerkeleyGame")
        
        game_state = data["game_state"]
        
        # Import here to avoid circular import
        from kriegspiel.berkeley import BerkeleyGame
        
        # Create new game instance
        game = BerkeleyGame(any_rule=game_state["any_rule"])
        
        # Restore board state
        try:
            game._board = chess.Board(game_state["board_fen"])
        except ValueError as e:
            raise MalformedDataError(f"Invalid board FEN: {game_state['board_fen']}") from e
            
        game._must_use_pawns = game_state["must_use_pawns"]
        game._game_over = game_state["game_over"]
        
        # Restore scoresheets
        game._whites_scoresheet = deserialize_kriegspiel_scoresheet(game_state["white_scoresheet"])
        game._blacks_scoresheet = deserialize_kriegspiel_scoresheet(game_state["black_scoresheet"])
        
        # Regenerate possible moves list for current position
        game._generate_possible_to_ask_list()
        
        return game
    except (KeyError, TypeError) as e:
        raise MalformedDataError(f"Invalid BerkeleyGame data structure") from e


def save_game_to_json(game, filename: str) -> None:
    """Save BerkeleyGame to JSON file."""
    try:
        data = serialize_berkeley_game(game)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, cls=KriegspielJSONEncoder)
    except (IOError, OSError) as e:
        raise SerializationError(f"Failed to save game to {filename}") from e


def load_game_from_json(filename: str):
    """Load BerkeleyGame from JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return deserialize_berkeley_game(data)
    except (IOError, OSError) as e:
        raise SerializationError(f"Failed to load game from {filename}") from e
    except json.JSONDecodeError as e:
        raise MalformedDataError(f"Invalid JSON in file {filename}") from e