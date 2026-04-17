# Release Notes

## Kriegspiel v. 1.2.3

- **Canonical Engine State**: `BerkeleyGame` serialization now stores `possible_to_ask`, so active turns can be resumed without losing question-state
- **Stable Schema Versioning**: serialization compatibility now uses a dedicated `schema_version` instead of tying saved payloads to the package version
- **Safety**: canonical payloads still validate `move_stack` against `board_fen` and scoresheet-derived moves before loading

## Kriegspiel v. 1.2.2

- **README Refresh**: simplified the package overview and trimmed maintainer-focused setup details from the published project description

## Kriegspiel v. 1.2.1

- **Serialization Integrity**: `BerkeleyGame` payloads now require `move_stack` and validate it against `board_fen` during deserialization
- **Safety**: malformed or inconsistent move history now fails fast instead of silently falling back to board-only restoration
- **Testing**: serialization coverage remains at 100% with explicit checks for missing and invalid `move_stack`

## Kriegspiel v. 1.1.2

- **Major Documentation Improvement**: Added comprehensive docstrings to all classes and methods
- **Code Quality**: Fixed typo in method name `_generate_possible_pawn_captures`
- **Validation Enhancement**: Resolved TODO comments with proper input validation and error messages
- **Testing**: Added comprehensive test coverage for edge cases, maintained 100% coverage
- **Developer Experience**: Enhanced README with better test instructions using `run_tests.py`
- **API Documentation**: All public methods now have detailed Args/Returns/Raises sections
- **Performance Notes**: Added documentation for known performance bottlenecks

## Kriegspiel v. 1.1.1

- Improved test coverage.
- PyPI upload fixed.
- Minor bug fixes.

## Kriegspiel v. 1.1.0

- Scoresheets are added as base functionality into `move.py` module.

## Kriegspiel v. 1.0.0

- Base version with `move.py` logic of Kriegspiel.
- Berkley rules with ANY option added.
