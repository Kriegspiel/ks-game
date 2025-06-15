# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python implementation of the Kriegspiel chess variant, a form of chess where players cannot see their opponent's pieces. The project currently supports Berkeley Kriegspiel rules with optional "Any" rule extension.

## Core Architecture

The codebase is organized around three main components:

1. **kriegspiel/move.py**: Core data structures for Kriegspiel game mechanics
   - `KriegspielMove`: Represents player questions/moves with question types (COMMON, ASK_ANY)
   - `KriegspielAnswer`: Referee responses with main announcements and special cases
   - `KriegspielScoresheet`: Tracks game history for each player
   - Enums for question types, announcements, and special cases

2. **kriegspiel/berkeley.py**: Main game engine implementing Berkeley Kriegspiel rules
   - `BerkeleyGame`: Server-side referee that knows full board state
   - Handles player questions via `ask_for()` method
   - Manages visible board state for each player
   - Implements "Any" rule for pawn capture detection

3. **Communication Pattern**: The game uses a question-answer protocol where:
   - Players ask questions about moves they want to make
   - Referee responds with legality and consequences
   - Players only see their own pieces and capture squares
   - Special announcements for checks, checkmates, draws

## Dependencies

- **python-chess**: Core chess logic and board representation
- **pytest**: Testing framework with coverage support
- **black**: Code formatting (line length 128)

## Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_berkeley.py
python -m pytest tests/test_move.py
```

### Code Formatting
```bash
# Format code with black (line length 128)
black -l 128 <file>
```

### Build and Distribution
```bash
# Build package
python -m build

# Upload to PyPI
twine upload dist/*
```

## Key Implementation Details

- Game state is maintained on server side (BerkeleyGame class)
- Players interact through KriegspielMove questions
- Referee maintains both full board and player-visible board states
- Pawn capture detection via "Any" rule creates tactical complexity
- Special case announcements for checks specify direction (rank/file/diagonal/knight)
- Scoresheet tracking maintains game history for both players