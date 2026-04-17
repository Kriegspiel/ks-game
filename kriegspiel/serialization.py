# -*- coding: utf-8 -*-

"""
JSON serialization support for Kriegspiel game state.

This module provides comprehensive serialization and deserialization for all
Kriegspiel game components using JSON format with custom encoders/decoders.

JSON Schema Structure:
{
  "schema_version": 3,
  "library_version": "1.2.3",
  "game_type": "BerkeleyGame",
  "game_state": {
    "any_rule": bool,
    "board_fen": str,
    "move_stack": [str],  // UCI moves used to verify board reconstruction
    "must_use_pawns": bool,
    "game_over": bool,
    "possible_to_ask": [...],  // Serialized KriegspielMove values for exact turn-state recovery
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

LEGACY_SERIALIZATION_SCHEMA_VERSION = 2
SERIALIZATION_SCHEMA_VERSION = 3


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


def serialize_possible_to_ask(moves: List[KriegspielMove]) -> List[Dict[str, Any]]:
    """Serialize current turn-state questions in a stable order."""
    serialized = [serialize_kriegspiel_move(move) for move in moves]
    serialized.sort(key=lambda item: (item["question_type"], item["chess_move"] or ""))
    return serialized


def deserialize_possible_to_ask(data: Any) -> List[KriegspielMove]:
    """Deserialize serialized possible_to_ask entries."""
    if not isinstance(data, list):
        raise MalformedDataError("Invalid possible_to_ask: expected a list of KriegspielMove values")
    return [deserialize_kriegspiel_move(item) for item in data]


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
        "schema_version": SERIALIZATION_SCHEMA_VERSION,
        "library_version": __version__,
        "game_type": "BerkeleyGame",
        "game_state": {
            "any_rule": game._any_rule,
            "board_fen": game._board.fen(),
            "move_stack": [move.uci() for move in game._board.move_stack],
            "must_use_pawns": game._must_use_pawns,
            "game_over": game._game_over,
            "possible_to_ask": serialize_possible_to_ask(game.possible_to_ask),
            "white_scoresheet": serialize_kriegspiel_scoresheet(game._whites_scoresheet),
            "black_scoresheet": serialize_kriegspiel_scoresheet(game._blacks_scoresheet)
        }
    }


def deserialize_berkeley_game(data: Dict[str, Any]):
    """Deserialize dictionary to BerkeleyGame."""
    try:
        # Check schema compatibility. Legacy payloads used `version` instead.
        schema_version = data.get("schema_version")
        if schema_version is None:
            schema_version = LEGACY_SERIALIZATION_SCHEMA_VERSION if "version" in data else "unknown"
        if schema_version not in {LEGACY_SERIALIZATION_SCHEMA_VERSION, SERIALIZATION_SCHEMA_VERSION}:
            raise UnsupportedVersionError(f"Unsupported schema_version: {schema_version}")
        
        # Check game type
        game_type = data.get("game_type", "unknown")
        if game_type != "BerkeleyGame":
            raise MalformedDataError(f"Invalid game type: {game_type}. Expected: BerkeleyGame")
        
        game_state = data["game_state"]
        
        # Import here to avoid circular import
        from kriegspiel.berkeley import BerkeleyGame
        
        # Create new game instance
        game = BerkeleyGame(any_rule=game_state["any_rule"])
        
        # Validate the stored FEN even when we can rebuild from move history.
        try:
            fen_board = chess.Board(game_state["board_fen"])
        except ValueError as e:
            raise MalformedDataError(f"Invalid board FEN: {game_state['board_fen']}") from e

        if "move_stack" not in game_state:
            raise MalformedDataError("Missing move_stack in BerkeleyGame data")

        move_stack = game_state["move_stack"]
        if not isinstance(move_stack, list):
            raise MalformedDataError("Invalid move_stack: expected a list of UCI moves")

        board = chess.Board()
        try:
            for move_uci in move_stack:
                if not isinstance(move_uci, str):
                    raise MalformedDataError(f"Invalid move_stack entry: {move_uci}")
                board.push_uci(move_uci)
        except ValueError as e:
            raise MalformedDataError(f"Invalid move_stack entry: {move_uci}") from e

        if board.fen() != game_state["board_fen"]:
            raise MalformedDataError("Serialized move_stack does not match board_fen")
        game._board = board
            
        game._must_use_pawns = game_state["must_use_pawns"]
        game._game_over = game_state["game_over"]
        
        # Restore scoresheets
        game._whites_scoresheet = deserialize_kriegspiel_scoresheet(game_state["white_scoresheet"])
        game._blacks_scoresheet = deserialize_kriegspiel_scoresheet(game_state["black_scoresheet"])

        scoresheet_move_stack = _move_stack_from_scoresheets(game._whites_scoresheet, game._blacks_scoresheet)
        if scoresheet_move_stack != move_stack:
            raise MalformedDataError("Scoresheet-derived moves do not match move_stack")

        if schema_version == SERIALIZATION_SCHEMA_VERSION:
            if "possible_to_ask" not in game_state:
                raise MalformedDataError("Missing possible_to_ask in BerkeleyGame data")
            game._possible_to_ask = deserialize_possible_to_ask(game_state["possible_to_ask"])
        else:
            # Legacy saved payloads did not preserve exact turn-state questions.
            game._generate_possible_to_ask_list()
            if game._must_use_pawns:
                game._possible_to_ask = list(game._generate_possible_pawn_captures())
        
        return game
    except (KeyError, TypeError) as e:
        raise MalformedDataError(f"Invalid BerkeleyGame data structure") from e


def _move_stack_from_scoresheets(white_scoresheet: KriegspielScoresheet, black_scoresheet: KriegspielScoresheet) -> List[str]:
    """Extract the executed chess moves recorded in both players' own scoresheets."""
    extracted: List[str] = []
    max_turns = max(len(white_scoresheet.moves_own), len(black_scoresheet.moves_own))

    for turn_index in range(max_turns):
        if turn_index < len(white_scoresheet.moves_own):
            extracted.extend(_completed_moves_from_turn(white_scoresheet.moves_own[turn_index]))
        if turn_index < len(black_scoresheet.moves_own):
            extracted.extend(_completed_moves_from_turn(black_scoresheet.moves_own[turn_index]))

    return extracted


def _completed_moves_from_turn(turn: List[Tuple[KriegspielMove, KriegspielAnswer]]) -> List[str]:
    """Return UCI moves for successful COMMON questions within a single turn."""
    completed_moves: List[str] = []
    for move, answer in turn:
        if move.question_type != QuestionAnnouncement.COMMON or not answer.move_done:
            continue
        if move.chess_move is None:
            raise MalformedDataError("Scoresheet move is missing chess_move")
        completed_moves.append(move.chess_move.uci())

    if len(completed_moves) > 1:
        raise MalformedDataError("Scoresheet turn contains multiple completed moves")

    return completed_moves


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
