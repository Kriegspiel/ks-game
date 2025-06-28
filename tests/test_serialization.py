# -*- coding: utf-8 -*-

import pytest
import json
import tempfile
import os
import chess

from kriegspiel.move import (
    QuestionAnnouncement, MainAnnouncement, SpecialCaseAnnouncement,
    KriegspielMove, KriegspielAnswer, KriegspielScoresheet
)
from kriegspiel.berkeley import BerkeleyGame
from kriegspiel.serialization import (
    serialize_chess_move, deserialize_chess_move,
    serialize_enum, deserialize_question_announcement, deserialize_main_announcement, 
    deserialize_special_case_announcement,
    serialize_kriegspiel_move, deserialize_kriegspiel_move,
    serialize_kriegspiel_answer, deserialize_kriegspiel_answer,
    serialize_kriegspiel_scoresheet, deserialize_kriegspiel_scoresheet,
    serialize_berkeley_game, deserialize_berkeley_game,
    save_game_to_json, load_game_from_json,
    KriegspielJSONEncoder,
    SerializationError, UnsupportedVersionError, MalformedDataError
)


class TestChessMoveSerializer:
    """Test chess.Move serialization/deserialization."""
    
    def test_serialize_chess_move(self):
        move = chess.Move.from_uci("e2e4")
        result = serialize_chess_move(move)
        assert result == "e2e4"
    
    def test_serialize_chess_move_none(self):
        result = serialize_chess_move(None)
        assert result is None
    
    def test_deserialize_chess_move(self):
        result = deserialize_chess_move("e2e4")
        expected = chess.Move.from_uci("e2e4")
        assert result == expected
    
    def test_deserialize_chess_move_none(self):
        result = deserialize_chess_move(None)
        assert result is None
    
    def test_chess_move_roundtrip(self):
        moves = [
            chess.Move.from_uci("e2e4"),
            chess.Move.from_uci("g1f3"),
            chess.Move.from_uci("e7e8q"),  # Promotion
            chess.Move.from_uci("e1g1"),   # Castling
        ]
        for move in moves:
            serialized = serialize_chess_move(move)
            deserialized = deserialize_chess_move(serialized)
            assert move == deserialized


class TestEnumSerializer:
    """Test enum serialization/deserialization."""
    
    def test_serialize_enum(self):
        assert serialize_enum(QuestionAnnouncement.COMMON) == "COMMON"
        assert serialize_enum(MainAnnouncement.REGULAR_MOVE) == "REGULAR_MOVE"
        assert serialize_enum(SpecialCaseAnnouncement.CHECK_RANK) == "CHECK_RANK"
    
    def test_deserialize_question_announcement(self):
        assert deserialize_question_announcement("COMMON") == QuestionAnnouncement.COMMON
        assert deserialize_question_announcement("ASK_ANY") == QuestionAnnouncement.ASK_ANY
    
    def test_deserialize_main_announcement(self):
        assert deserialize_main_announcement("REGULAR_MOVE") == MainAnnouncement.REGULAR_MOVE
        assert deserialize_main_announcement("CAPTURE_DONE") == MainAnnouncement.CAPTURE_DONE
    
    def test_deserialize_special_case_announcement(self):
        assert deserialize_special_case_announcement("NONE") == SpecialCaseAnnouncement.NONE
        assert deserialize_special_case_announcement("CHECK_RANK") == SpecialCaseAnnouncement.CHECK_RANK
    
    def test_enum_roundtrip(self):
        enums_to_test = [
            (QuestionAnnouncement.COMMON, deserialize_question_announcement),
            (QuestionAnnouncement.ASK_ANY, deserialize_question_announcement),
            (MainAnnouncement.REGULAR_MOVE, deserialize_main_announcement),
            (MainAnnouncement.CAPTURE_DONE, deserialize_main_announcement),
            (MainAnnouncement.ILLEGAL_MOVE, deserialize_main_announcement),
            (SpecialCaseAnnouncement.NONE, deserialize_special_case_announcement),
            (SpecialCaseAnnouncement.CHECK_RANK, deserialize_special_case_announcement),
            (SpecialCaseAnnouncement.CHECKMATE_WHITE_WINS, deserialize_special_case_announcement),
        ]
        
        for enum_val, deserializer in enums_to_test:
            serialized = serialize_enum(enum_val)
            deserialized = deserializer(serialized)
            assert enum_val == deserialized


class TestKriegspielMoveSerializer:
    """Test KriegspielMove serialization/deserialization."""
    
    def test_serialize_common_move(self):
        move = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4"))
        result = serialize_kriegspiel_move(move)
        expected = {
            "question_type": "COMMON",
            "chess_move": "e2e4"
        }
        assert result == expected
    
    def test_serialize_ask_any_move(self):
        move = KriegspielMove(QuestionAnnouncement.ASK_ANY)
        result = serialize_kriegspiel_move(move)
        expected = {
            "question_type": "ASK_ANY",
            "chess_move": None
        }
        assert result == expected
    
    def test_deserialize_common_move(self):
        data = {
            "question_type": "COMMON",
            "chess_move": "e2e4"
        }
        result = deserialize_kriegspiel_move(data)
        expected = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4"))
        assert result == expected
    
    def test_deserialize_ask_any_move(self):
        data = {
            "question_type": "ASK_ANY",
            "chess_move": None
        }
        result = deserialize_kriegspiel_move(data)
        expected = KriegspielMove(QuestionAnnouncement.ASK_ANY)
        assert result == expected
    
    def test_kriegspiel_move_roundtrip(self):
        moves = [
            KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4")),
            KriegspielMove(QuestionAnnouncement.ASK_ANY),
            KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e8q")),
        ]
        
        for move in moves:
            serialized = serialize_kriegspiel_move(move)
            deserialized = deserialize_kriegspiel_move(serialized)
            assert move == deserialized


class TestKriegspielAnswerSerializer:
    """Test KriegspielAnswer serialization/deserialization."""
    
    def test_serialize_regular_move_answer(self):
        answer = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE)
        result = serialize_kriegspiel_answer(answer)
        expected = {
            "main_announcement": "REGULAR_MOVE",
            "capture_at_square": None,
            "special_announcement": "NONE",
            "check_1": None,
            "check_2": None
        }
        assert result == expected
    
    def test_serialize_capture_answer(self):
        answer = KriegspielAnswer(MainAnnouncement.CAPTURE_DONE, capture_at_square=28)
        result = serialize_kriegspiel_answer(answer)
        expected = {
            "main_announcement": "CAPTURE_DONE",
            "capture_at_square": 28,
            "special_announcement": "NONE",
            "check_1": None,
            "check_2": None
        }
        assert result == expected
    
    def test_serialize_check_answer(self):
        answer = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE, 
                                special_announcement=SpecialCaseAnnouncement.CHECK_RANK)
        result = serialize_kriegspiel_answer(answer)
        expected = {
            "main_announcement": "REGULAR_MOVE",
            "capture_at_square": None,
            "special_announcement": "CHECK_RANK",
            "check_1": None,
            "check_2": None
        }
        assert result == expected
    
    def test_serialize_double_check_answer(self):
        answer = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE,
                                special_announcement=(SpecialCaseAnnouncement.CHECK_DOUBLE, 
                                                    [SpecialCaseAnnouncement.CHECK_RANK, 
                                                     SpecialCaseAnnouncement.CHECK_FILE]))
        result = serialize_kriegspiel_answer(answer)
        expected = {
            "main_announcement": "REGULAR_MOVE",
            "capture_at_square": None,
            "special_announcement": "CHECK_DOUBLE",
            "check_1": "CHECK_RANK",
            "check_2": "CHECK_FILE"
        }
        assert result == expected
    
    def test_deserialize_regular_move_answer(self):
        data = {
            "main_announcement": "REGULAR_MOVE",
            "capture_at_square": None,
            "special_announcement": "NONE",
            "check_1": None,
            "check_2": None
        }
        result = deserialize_kriegspiel_answer(data)
        expected = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE)
        assert result == expected
    
    def test_deserialize_capture_answer(self):
        data = {
            "main_announcement": "CAPTURE_DONE",
            "capture_at_square": 28,
            "special_announcement": "NONE",
            "check_1": None,
            "check_2": None
        }
        result = deserialize_kriegspiel_answer(data)
        expected = KriegspielAnswer(MainAnnouncement.CAPTURE_DONE, capture_at_square=28)
        assert result == expected
    
    def test_deserialize_double_check_answer(self):
        data = {
            "main_announcement": "REGULAR_MOVE",
            "capture_at_square": None,
            "special_announcement": "CHECK_DOUBLE",
            "check_1": "CHECK_RANK",
            "check_2": "CHECK_FILE"
        }
        result = deserialize_kriegspiel_answer(data)
        expected = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE,
                                  special_announcement=(SpecialCaseAnnouncement.CHECK_DOUBLE,
                                                      [SpecialCaseAnnouncement.CHECK_RANK,
                                                       SpecialCaseAnnouncement.CHECK_FILE]))
        assert result == expected
    
    def test_kriegspiel_answer_roundtrip(self):
        answers = [
            KriegspielAnswer(MainAnnouncement.REGULAR_MOVE),
            KriegspielAnswer(MainAnnouncement.CAPTURE_DONE, capture_at_square=28),
            KriegspielAnswer(MainAnnouncement.ILLEGAL_MOVE),
            KriegspielAnswer(MainAnnouncement.REGULAR_MOVE, 
                           special_announcement=SpecialCaseAnnouncement.CHECK_RANK),
            KriegspielAnswer(MainAnnouncement.REGULAR_MOVE,
                           special_announcement=(SpecialCaseAnnouncement.CHECK_DOUBLE,
                                               [SpecialCaseAnnouncement.CHECK_RANK,
                                                SpecialCaseAnnouncement.CHECK_FILE])),
            KriegspielAnswer(MainAnnouncement.HAS_ANY),
            KriegspielAnswer(MainAnnouncement.NO_ANY),
        ]
        
        for answer in answers:
            serialized = serialize_kriegspiel_answer(answer)
            deserialized = deserialize_kriegspiel_answer(serialized)
            assert answer == deserialized


class TestKriegspielScoresheetSerializer:
    """Test KriegspielScoresheet serialization/deserialization."""
    
    def test_serialize_empty_scoresheet(self):
        scoresheet = KriegspielScoresheet(chess.WHITE)
        result = serialize_kriegspiel_scoresheet(scoresheet)
        expected = {
            "color": "WHITE",
            "moves_own": [],
            "moves_opponent": [],
            "last_move_number": 0
        }
        assert result == expected
    
    def test_serialize_scoresheet_with_moves(self):
        scoresheet = KriegspielScoresheet(chess.BLACK)
        
        # Add some moves
        move1 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e5"))
        answer1 = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE)
        scoresheet.record_move_own(move1, answer1)
        
        scoresheet.record_move_opponent(QuestionAnnouncement.COMMON, 
                                      KriegspielAnswer(MainAnnouncement.REGULAR_MOVE))
        
        result = serialize_kriegspiel_scoresheet(scoresheet)
        
        assert result["color"] == "BLACK"
        assert len(result["moves_own"]) == 1
        assert len(result["moves_opponent"]) == 1
        assert result["last_move_number"] == 1
    
    def test_deserialize_empty_scoresheet(self):
        data = {
            "color": "WHITE", 
            "moves_own": [],
            "moves_opponent": [],
            "last_move_number": 0
        }
        result = deserialize_kriegspiel_scoresheet(data)
        
        assert result.color == chess.WHITE
        assert result.moves_own == []
        assert result.moves_opponent == []
    
    def test_kriegspiel_scoresheet_roundtrip(self):
        scoresheet = KriegspielScoresheet(chess.BLACK)
        
        # Add moves to test full functionality
        move1 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e5"))
        answer1 = KriegspielAnswer(MainAnnouncement.REGULAR_MOVE)
        scoresheet.record_move_own(move1, answer1)
        
        move2 = KriegspielMove(QuestionAnnouncement.ASK_ANY)
        answer2 = KriegspielAnswer(MainAnnouncement.NO_ANY)
        scoresheet.record_move_own(move2, answer2)
        
        scoresheet.record_move_opponent(QuestionAnnouncement.COMMON,
                                      KriegspielAnswer(MainAnnouncement.CAPTURE_DONE, capture_at_square=28))
        
        serialized = serialize_kriegspiel_scoresheet(scoresheet)
        deserialized = deserialize_kriegspiel_scoresheet(serialized)
        
        assert deserialized.color == scoresheet.color
        assert len(deserialized.moves_own) == len(scoresheet.moves_own)
        assert len(deserialized.moves_opponent) == len(scoresheet.moves_opponent)


class TestBerkeleyGameSerializer:
    """Test BerkeleyGame serialization/deserialization."""
    
    def test_serialize_initial_game(self):
        game = BerkeleyGame(any_rule=True)
        result = serialize_berkeley_game(game)
        
        assert result["version"] == "1.2.0"
        assert result["game_type"] == "BerkeleyGame"
        assert result["game_state"]["any_rule"] is True
        assert result["game_state"]["board_fen"] == chess.Board().fen()
        assert result["game_state"]["must_use_pawns"] is False
        assert result["game_state"]["game_over"] is False
        assert "white_scoresheet" in result["game_state"]
        assert "black_scoresheet" in result["game_state"]
    
    def test_serialize_game_with_moves(self):
        game = BerkeleyGame(any_rule=True)
        
        # Make some moves
        move1 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4"))
        answer1 = game.ask_for(move1)
        
        move2 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e5"))
        answer2 = game.ask_for(move2)
        
        result = serialize_berkeley_game(game)
        
        # Check that moves are recorded in scoresheets
        white_moves = result["game_state"]["white_scoresheet"]["moves_own"]
        black_moves = result["game_state"]["black_scoresheet"]["moves_own"]
        
        assert len(white_moves) == 1
        assert len(black_moves) == 1
    
    def test_deserialize_initial_game(self):
        original_game = BerkeleyGame(any_rule=False)
        serialized = serialize_berkeley_game(original_game)
        deserialized = deserialize_berkeley_game(serialized)
        
        assert deserialized._any_rule == original_game._any_rule
        assert deserialized._board.fen() == original_game._board.fen()
        assert deserialized._must_use_pawns == original_game._must_use_pawns
        assert deserialized._game_over == original_game._game_over
        assert deserialized.turn == original_game.turn
    
    def test_berkeley_game_roundtrip(self):
        game = BerkeleyGame(any_rule=True)
        
        # Make several moves to test state preservation
        moves_to_test = [
            chess.Move.from_uci("e2e4"),
            chess.Move.from_uci("e7e5"),
            chess.Move.from_uci("g1f3"),
            chess.Move.from_uci("b8c6"),
        ]
        
        for move_uci in moves_to_test:
            if game.game_over:
                break
            move = KriegspielMove(QuestionAnnouncement.COMMON, move_uci)
            if game.is_possible_to_ask(move):
                game.ask_for(move)
        
        # Serialize and deserialize
        serialized = serialize_berkeley_game(game)
        deserialized = deserialize_berkeley_game(serialized)
        
        # Check that game state is preserved
        assert deserialized._any_rule == game._any_rule
        assert deserialized._board.fen() == game._board.fen()
        assert deserialized._must_use_pawns == game._must_use_pawns
        assert deserialized._game_over == game._game_over
        assert deserialized.turn == game.turn
        
        # Check that scoresheets are preserved
        assert len(deserialized._whites_scoresheet.moves_own) == len(game._whites_scoresheet.moves_own)
        assert len(deserialized._blacks_scoresheet.moves_own) == len(game._blacks_scoresheet.moves_own)


class TestFileOperations:
    """Test save/load game to/from files."""
    
    def test_save_and_load_game(self):
        game = BerkeleyGame(any_rule=True)
        
        # Make some moves
        move1 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4"))
        game.ask_for(move1)
        
        move2 = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e5"))
        game.ask_for(move2)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_filename = f.name
        
        try:
            save_game_to_json(game, temp_filename)
            
            # Load from file
            loaded_game = load_game_from_json(temp_filename)
            
            # Verify game state is preserved
            assert loaded_game._any_rule == game._any_rule
            assert loaded_game._board.fen() == game._board.fen()
            assert loaded_game.turn == game.turn
            
        finally:
            os.unlink(temp_filename)
    
    def test_berkeley_game_save_load_methods(self):
        game = BerkeleyGame(any_rule=False)
        
        # Make a move
        move = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("d2d4"))
        game.ask_for(move)
        
        # Save using instance method
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_filename = f.name
        
        try:
            game.save_game(temp_filename)
            
            # Load using class method
            loaded_game = BerkeleyGame.load_game(temp_filename)
            
            # Verify
            assert loaded_game._any_rule == game._any_rule
            assert loaded_game._board.fen() == game._board.fen()
            assert loaded_game.turn == game.turn
            
        finally:
            os.unlink(temp_filename)


class TestJSONEncoder:
    """Test custom JSON encoder."""
    
    def test_json_encoder_with_game(self):
        game = BerkeleyGame()
        
        # This should work without raising exceptions
        json_str = json.dumps(game, cls=KriegspielJSONEncoder, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "version" in parsed
        assert "game_type" in parsed  
        assert "game_state" in parsed
    
    def test_json_encoder_with_move(self):
        move = KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4"))
        
        json_str = json.dumps(move, cls=KriegspielJSONEncoder)
        parsed = json.loads(json_str)
        
        assert parsed["question_type"] == "COMMON"
        assert parsed["chess_move"] == "e2e4"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_serialize_game_with_any_rule_false(self):
        game = BerkeleyGame(any_rule=False)
        result = serialize_berkeley_game(game)
        
        assert result["game_state"]["any_rule"] is False
        
        # Deserialize and verify
        deserialized = deserialize_berkeley_game(result)
        assert deserialized._any_rule is False
    
    def test_serialize_game_after_any_question(self):
        game = BerkeleyGame(any_rule=True)
        
        # Ask ANY question
        any_move = KriegspielMove(QuestionAnnouncement.ASK_ANY)
        answer = game.ask_for(any_move)
        
        # Serialize current state
        result = serialize_berkeley_game(game)
        deserialized = deserialize_berkeley_game(result)
        
        # Verify state is preserved
        assert deserialized._must_use_pawns == game._must_use_pawns
    
    def test_complex_game_scenario(self):
        """Test serialization of a complex game with multiple move types."""
        game = BerkeleyGame(any_rule=True)
        
        # Sequence of different move types
        moves = [
            KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e2e4")),
            KriegspielMove(QuestionAnnouncement.ASK_ANY),  # Should get NO_ANY
            KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("e7e5")),
            KriegspielMove(QuestionAnnouncement.COMMON, chess.Move.from_uci("g1f3")),
        ]
        
        for move in moves:
            if game.is_possible_to_ask(move):
                game.ask_for(move)
        
        # Serialize and deserialize
        serialized = serialize_berkeley_game(game)
        deserialized = deserialize_berkeley_game(serialized)
        
        # Verify complex state preservation
        assert deserialized._board.fen() == game._board.fen()
        assert len(deserialized._whites_scoresheet.moves_own) == len(game._whites_scoresheet.moves_own)
        assert len(deserialized._blacks_scoresheet.moves_own) == len(game._blacks_scoresheet.moves_own)


class TestErrorHandling:
    """Test error handling and malformed data scenarios."""
    
    def test_invalid_uci_move(self):
        with pytest.raises(MalformedDataError, match="Invalid UCI move string"):
            deserialize_chess_move("invalid_move")
    
    def test_invalid_question_announcement(self):
        with pytest.raises(MalformedDataError, match="Invalid QuestionAnnouncement"):
            deserialize_question_announcement("INVALID_TYPE")
    
    def test_invalid_main_announcement(self):
        with pytest.raises(MalformedDataError, match="Invalid MainAnnouncement"):
            deserialize_main_announcement("INVALID_TYPE")
    
    def test_invalid_special_case_announcement(self):
        with pytest.raises(MalformedDataError, match="Invalid SpecialCaseAnnouncement"):
            deserialize_special_case_announcement("INVALID_TYPE")
    
    def test_malformed_kriegspiel_move_data(self):
        with pytest.raises(MalformedDataError, match="Invalid KriegspielMove data"):
            deserialize_kriegspiel_move({"missing_field": "value"})
    
    def test_malformed_kriegspiel_answer_data(self):
        with pytest.raises(MalformedDataError, match="Invalid KriegspielAnswer data"):
            deserialize_kriegspiel_answer({"missing_field": "value"})
    
    def test_malformed_scoresheet_data(self):
        with pytest.raises(MalformedDataError, match="Invalid KriegspielScoresheet data"):
            deserialize_kriegspiel_scoresheet({"missing_field": "value"})
    
    def test_unsupported_version(self):
        data = {
            "version": "2.0",
            "game_type": "BerkeleyGame",
            "game_state": {}
        }
        with pytest.raises(UnsupportedVersionError, match="Unsupported version: 2.0"):
            deserialize_berkeley_game(data)
    
    def test_malformed_berkeley_game_data(self):
        # Test with correct version but missing game_state
        data = {"version": "1.2.0", "game_type": "BerkeleyGame", "invalid": "data"}
        with pytest.raises(MalformedDataError, match="Invalid BerkeleyGame data structure"):
            deserialize_berkeley_game(data)
    
    def test_invalid_board_fen(self):
        data = {
            "version": "1.2.0",
            "game_type": "BerkeleyGame",
            "game_state": {
                "any_rule": True,
                "board_fen": "invalid_fen_string",
                "must_use_pawns": False,
                "game_over": False,
                "white_scoresheet": {
                    "color": "WHITE",
                    "moves_own": [],
                    "moves_opponent": [],
                    "last_move_number": 0
                },
                "black_scoresheet": {
                    "color": "BLACK",
                    "moves_own": [],
                    "moves_opponent": [],
                    "last_move_number": 0
                }
            }
        }
        with pytest.raises(MalformedDataError, match="Invalid board FEN"):
            deserialize_berkeley_game(data)
    
    def test_invalid_game_type(self):
        data = {
            "version": "1.2.0",
            "game_type": "SomeOtherGame",
            "game_state": {}
        }
        with pytest.raises(MalformedDataError, match="Invalid game type: SomeOtherGame"):
            deserialize_berkeley_game(data)
    
    def test_save_to_invalid_path(self):
        game = BerkeleyGame()
        with pytest.raises(SerializationError, match="Failed to save game"):
            save_game_to_json(game, "/invalid/path/game.json")
    
    def test_load_from_nonexistent_file(self):
        with pytest.raises(SerializationError, match="Failed to load game"):
            load_game_from_json("/nonexistent/file.json")
    
    def test_load_invalid_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("{invalid json content")
            temp_filename = f.name
        
        try:
            with pytest.raises(MalformedDataError, match="Invalid JSON"):
                load_game_from_json(temp_filename)
        finally:
            os.unlink(temp_filename)
    
    def test_berkeley_game_save_error_handling(self):
        game = BerkeleyGame()
        with pytest.raises(SerializationError):
            game.save_game("/invalid/path/game.json")
    
    def test_berkeley_game_load_error_handling(self):
        with pytest.raises(SerializationError):
            BerkeleyGame.load_game("/nonexistent/file.json")