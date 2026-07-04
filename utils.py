"""
utils.py

Shared constants, custom exception types, and standalone helper
utilities (puzzle generation and difficulty estimation) used across
the Sudoku solver project.
"""

from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from board import SudokuBoard

GRID_SIZE: int = 9
BOX_SIZE: int = 3
EMPTY_CELL: int = 0


class SudokuError(Exception):
    """Base class for all Sudoku-related errors."""


class InvalidDimensionError(SudokuError):
    """Raised when a board does not have the required 9x9 shape."""


class InvalidValueError(SudokuError):
    """Raised when a cell contains a value outside the 0-9 range."""


class InvalidPlacementError(SudokuError):
    """Raised when the initial board violates Sudoku's placement rules."""


def generate_solved_grid() -> List[List[int]]:
    """Generate a complete, randomly-shuffled, valid solved Sudoku grid.

    Uses backtracking with randomized candidate order, which is an
    efficient way to construct a full valid solution from scratch.

    Returns:
        A 9x9 list of lists containing a complete valid Sudoku solution.
    """
    grid: List[List[int]] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def is_safe(row: int, col: int, num: int) -> bool:
        if num in grid[row]:
            return False
        if num in (grid[r][col] for r in range(GRID_SIZE)):
            return False
        box_row = (row // BOX_SIZE) * BOX_SIZE
        box_col = (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if grid[r][c] == num:
                    return False
        return True

    def fill(pos: int = 0) -> bool:
        if pos == GRID_SIZE * GRID_SIZE:
            return True
        row, col = divmod(pos, GRID_SIZE)
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for num in numbers:
            if is_safe(row, col, num):
                grid[row][col] = num
                if fill(pos + 1):
                    return True
                grid[row][col] = 0
        return False

    fill()
    return grid


def generate_puzzle(clues: int = 30, seed: int | None = None) -> "SudokuBoard":
    """Generate a random, uniquely-solvable Sudoku puzzle.

    Args:
        clues: Approximate number of filled cells to leave in the final
            puzzle (the more clues, the easier the puzzle). Must be
            between 17 (the minimum known for a unique solution) and 81.
        seed: Optional random seed for reproducible puzzles.

    Returns:
        A SudokuBoard with `clues` (or slightly more) cells filled in,
        guaranteed to have exactly one solution.

    Raises:
        ValueError: If clues is outside the valid [17, 81] range.
    """
    # Local imports to avoid a circular import between board.py,
    # solver.py, and utils.py at module load time.
    from board import SudokuBoard
    from solver import SudokuSolver

    if not (17 <= clues <= 81):
        raise ValueError("clues must be between 17 and 81.")

    if seed is not None:
        random.seed(seed)

    solved = generate_solved_grid()
    puzzle = [row[:] for row in solved]

    cells: List[Tuple[int, int]] = [
        (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
    ]
    random.shuffle(cells)
    cells_to_remove = GRID_SIZE * GRID_SIZE - clues

    removed = 0
    for row, col in cells:
        if removed >= cells_to_remove:
            break
        backup = puzzle[row][col]
        puzzle[row][col] = EMPTY_CELL

        # Only keep the removal if the puzzle still has a unique solution.
        candidate_board = SudokuBoard(puzzle, validate=False)
        solver = SudokuSolver(candidate_board)
        if solver.count_solutions(limit=2) != 1:
            puzzle[row][col] = backup
        else:
            removed += 1

    return SudokuBoard(puzzle)


def estimate_difficulty(board: "SudokuBoard") -> str:
    """Estimate a puzzle's difficulty from its number of given clues.

    This is a simple heuristic (not a full solving-technique analysis)
    suitable for quick labeling of generated or loaded puzzles.

    Args:
        board: The SudokuBoard to evaluate.

    Returns:
        One of "Easy", "Medium", "Hard", or "Very Hard".
    """
    clues = sum(1 for row in board.grid for value in row if value != EMPTY_CELL)
    if clues >= 45:
        return "Easy"
    if clues >= 35:
        return "Medium"
    if clues >= 27:
        return "Hard"
    return "Very Hard"
