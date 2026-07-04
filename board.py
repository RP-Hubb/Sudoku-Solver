"""
board.py

Defines the SudokuBoard class, which represents a 9x9 Sudoku grid,
handles validation of the puzzle's structure and rules, and provides
clean, human-readable printing of the board.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from utils import (
    BOX_SIZE,
    EMPTY_CELL,
    GRID_SIZE,
    InvalidDimensionError,
    InvalidPlacementError,
    InvalidValueError,
)


class SudokuBoard:
    """Represents a 9x9 Sudoku board and enforces Sudoku's structural rules.

    Empty cells are represented internally by the integer 0.
    """

    def __init__(self, grid: List[List[int]], validate: bool = True) -> None:
        """Create a board from a 9x9 list of lists of ints (0-9).

        Args:
            grid: A 9x9 list of lists containing integers 0-9, where 0
                marks an empty cell.
            validate: If True (default), the grid's dimensions, value
                range, and rule-consistency are checked immediately.

        Raises:
            InvalidDimensionError: If the grid is not 9x9.
            InvalidValueError: If any cell is outside the 0-9 range.
            InvalidPlacementError: If the initial values violate Sudoku
                rules (duplicate values in a row, column, or box).
        """
        # Store a deep copy so external mutation of the input list
        # cannot silently corrupt the board's internal state.
        self.grid: List[List[int]] = [row[:] for row in grid]
        if validate:
            self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> None:
        """Validate dimensions, cell values, and rule-consistency.

        Raises:
            InvalidDimensionError: Wrong number of rows/columns.
            InvalidValueError: A cell value is not an int in [0, 9].
            InvalidPlacementError: Two identical non-zero digits share a
                row, column, or 3x3 box.
        """
        self._validate_dimensions()
        self._validate_values()
        self._validate_rules()

    def _validate_dimensions(self) -> None:
        if len(self.grid) != GRID_SIZE:
            raise InvalidDimensionError(
                f"Board must have {GRID_SIZE} rows, got {len(self.grid)}."
            )
        for i, row in enumerate(self.grid):
            if len(row) != GRID_SIZE:
                raise InvalidDimensionError(
                    f"Row {i} must have {GRID_SIZE} columns, got {len(row)}."
                )

    def _validate_values(self) -> None:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c]
                if not isinstance(value, int) or isinstance(value, bool):
                    raise InvalidValueError(
                        f"Cell ({r}, {c}) has non-integer value: {value!r}."
                    )
                if not 0 <= value <= 9:
                    raise InvalidValueError(
                        f"Cell ({r}, {c}) has out-of-range value: {value}."
                    )

    def _validate_rules(self) -> None:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c]
                if value == EMPTY_CELL:
                    continue
                # Temporarily clear the cell so the conflict check below
                # does not simply see the digit conflicting with itself.
                self.grid[r][c] = EMPTY_CELL
                conflicts = not self._is_placement_valid(r, c, value)
                self.grid[r][c] = value
                if conflicts:
                    raise InvalidPlacementError(
                        f"Duplicate value {value} conflicts at "
                        f"row {r}, column {c}."
                    )

    def _is_placement_valid(self, row: int, col: int, num: int) -> bool:
        """Check whether num could legally be placed at (row, col).

        Assumes (row, col) is currently empty (0). Used internally by
        validate() only; the solver has its own equivalent check.
        """
        if num in self.grid[row]:
            return False
        if num in (self.grid[r][col] for r in range(GRID_SIZE)):
            return False
        box_row = (row // BOX_SIZE) * BOX_SIZE
        box_col = (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if self.grid[r][c] == num:
                    return False
        return True

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get(self, row: int, col: int) -> int:
        """Return the value at (row, col)."""
        return self.grid[row][col]

    def set(self, row: int, col: int, value: int) -> None:
        """Set the value at (row, col) without re-validating the board."""
        self.grid[row][col] = value

    def is_full(self) -> bool:
        """Return True if there are no empty (0) cells left."""
        return all(EMPTY_CELL not in row for row in self.grid)

    def copy(self) -> "SudokuBoard":
        """Return a new, independent SudokuBoard with the same values."""
        return SudokuBoard(self.grid, validate=False)

    def to_list(self) -> List[List[int]]:
        """Return a plain, deep-copied list-of-lists representation."""
        return [row[:] for row in self.grid]

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------
    @classmethod
    def from_file(cls, path: str | Path) -> "SudokuBoard":
        """Load a puzzle from a text file.

        The file should contain 9 non-blank lines. Each line may either
        be 9 characters long (e.g. "53..7...."), or contain 9
        whitespace-separated tokens. Use '0' or '.' for empty cells.

        Args:
            path: Path to the puzzle text file.

        Returns:
            A validated SudokuBoard.

        Raises:
            InvalidDimensionError: If the file doesn't contain 9 usable rows.
            InvalidValueError: If a character can't be parsed as 0-9.
        """
        text = Path(path).read_text(encoding="utf-8")
        rows: List[List[int]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            tokens = stripped.split() if " " in stripped else list(stripped)
            row: List[int] = []
            for token in tokens:
                if token in (".", "0"):
                    row.append(0)
                elif token.isdigit():
                    row.append(int(token))
                else:
                    raise InvalidValueError(
                        f"Unrecognized character {token!r} in puzzle file."
                    )
            rows.append(row)
        return cls(rows)

    def to_file(self, path: str | Path) -> None:
        """Write the board to a text file, one row per line, '.' for empty."""
        lines = [
            "".join(str(v) if v != EMPTY_CELL else "." for v in row)
            for row in self.grid
        ]
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Render the board as a human-readable 9x9 grid with separators."""
        lines: List[str] = []
        for r in range(GRID_SIZE):
            if r != 0 and r % BOX_SIZE == 0:
                lines.append("------+-------+------")
            row_cells: List[str] = []
            for c in range(GRID_SIZE):
                if c != 0 and c % BOX_SIZE == 0:
                    row_cells.append("|")
                value = self.grid[r][c]
                row_cells.append(str(value) if value != EMPTY_CELL else ".")
            lines.append(" ".join(row_cells))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"SudokuBoard({self.grid!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SudokuBoard):
            return NotImplemented
        return self.grid == other.grid
