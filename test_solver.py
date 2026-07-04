"""
test_solver.py

Unit tests for the Sudoku Solver project, covering board validation,
placement rules, solving (easy/medium/hard/nearly-complete/already
solved), invalid board detection, solution counting, and hints.

Run with:
    python -m unittest test_solver.py -v
"""

from __future__ import annotations

import unittest

from board import SudokuBoard
from examples import (
    EASY_PUZZLE,
    HARD_PUZZLE,
    INVALID_PUZZLE,
    MEDIUM_PUZZLE,
    NEARLY_COMPLETE_PUZZLE,
    SOLVED_PUZZLE,
)
from solver import SudokuSolver
from utils import (
    InvalidDimensionError,
    InvalidPlacementError,
    InvalidValueError,
    estimate_difficulty,
    generate_puzzle,
)


def _is_full_and_valid(board: SudokuBoard) -> bool:
    """Helper: confirm a board is completely filled with no rule violations."""
    if not board.is_full():
        return False
    try:
        board.validate()
    except Exception:
        return False
    return True


class TestSudokuBoard(unittest.TestCase):
    """Tests for SudokuBoard construction, validation, and I/O."""

    def test_valid_board_constructs(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        self.assertEqual(board.get(0, 0), 5)
        self.assertEqual(board.get(0, 2), 0)

    def test_wrong_row_count_raises(self) -> None:
        bad_grid = [row[:] for row in EASY_PUZZLE[:-1]]  # only 8 rows
        with self.assertRaises(InvalidDimensionError):
            SudokuBoard(bad_grid)

    def test_wrong_column_count_raises(self) -> None:
        bad_grid = [row[:] for row in EASY_PUZZLE]
        bad_grid[0] = bad_grid[0][:-1]  # only 8 columns
        with self.assertRaises(InvalidDimensionError):
            SudokuBoard(bad_grid)

    def test_out_of_range_value_raises(self) -> None:
        bad_grid = [row[:] for row in EASY_PUZZLE]
        bad_grid[0][0] = 15
        with self.assertRaises(InvalidValueError):
            SudokuBoard(bad_grid)

    def test_duplicate_in_row_raises(self) -> None:
        with self.assertRaises(InvalidPlacementError):
            SudokuBoard(INVALID_PUZZLE)

    def test_is_full_detects_incomplete_board(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        self.assertFalse(board.is_full())

    def test_is_full_detects_complete_board(self) -> None:
        board = SudokuBoard(SOLVED_PUZZLE)
        self.assertTrue(board.is_full())

    def test_copy_is_independent(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        clone = board.copy()
        clone.set(0, 2, 9)
        self.assertEqual(board.get(0, 2), 0)
        self.assertEqual(clone.get(0, 2), 9)

    def test_str_contains_separators(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        text = str(board)
        self.assertIn("------+-------+------", text)
        self.assertIn("|", text)


class TestSudokuSolverValidity(unittest.TestCase):
    """Tests for the is_valid and find_empty primitives."""

    def setUp(self) -> None:
        self.board = SudokuBoard(EASY_PUZZLE)
        self.solver = SudokuSolver(self.board)

    def test_find_empty_returns_first_empty_cell(self) -> None:
        self.assertEqual(self.solver.find_empty(), (0, 2))

    def test_find_empty_returns_none_when_full(self) -> None:
        solved_board = SudokuBoard(SOLVED_PUZZLE)
        solver = SudokuSolver(solved_board)
        self.assertIsNone(solver.find_empty())

    def test_valid_placement_accepted(self) -> None:
        # 4 does not appear in row 0, column 2, or the top-left box.
        self.assertTrue(self.solver.is_valid(0, 2, 4))

    def test_invalid_placement_row_conflict(self) -> None:
        # 5 already appears in row 0.
        self.assertFalse(self.solver.is_valid(0, 2, 5))

    def test_invalid_placement_column_conflict(self) -> None:
        # 8 already appears in column 2 (row 2).
        self.assertFalse(self.solver.is_valid(0, 2, 8))

    def test_invalid_placement_box_conflict(self) -> None:
        # 9 already appears in the top-left 3x3 box (row 2, col 1).
        self.assertFalse(self.solver.is_valid(0, 2, 9))


class TestSudokuSolverSolving(unittest.TestCase):
    """Tests for full puzzle solving across difficulty levels."""

    def test_solve_easy_puzzle(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        solver = SudokuSolver(board)
        self.assertTrue(solver.solve())
        self.assertTrue(_is_full_and_valid(board))

    def test_solve_medium_puzzle(self) -> None:
        board = SudokuBoard(MEDIUM_PUZZLE)
        solver = SudokuSolver(board)
        self.assertTrue(solver.solve())
        self.assertTrue(_is_full_and_valid(board))

    def test_solve_hard_puzzle(self) -> None:
        board = SudokuBoard(HARD_PUZZLE)
        solver = SudokuSolver(board)
        self.assertTrue(solver.solve())
        self.assertTrue(_is_full_and_valid(board))

    def test_solve_nearly_complete_puzzle(self) -> None:
        board = SudokuBoard(NEARLY_COMPLETE_PUZZLE)
        solver = SudokuSolver(board)
        self.assertTrue(solver.solve())
        self.assertEqual(board.get(8, 8), 9)

    def test_already_solved_puzzle_stays_solved(self) -> None:
        board = SudokuBoard(SOLVED_PUZZLE)
        solver = SudokuSolver(board)
        self.assertTrue(solver.solve())
        self.assertEqual(board.to_list(), SOLVED_PUZZLE)

    def test_solve_easy_matches_known_solution(self) -> None:
        # The classic example puzzle has a well-known unique solution.
        board = SudokuBoard(EASY_PUZZLE)
        solver = SudokuSolver(board)
        solver.solve()
        self.assertEqual(board.to_list(), SOLVED_PUZZLE)


class TestSudokuSolverExtras(unittest.TestCase):
    """Tests for solution counting, hints, and step-by-step solving."""

    def test_count_solutions_unique_puzzle(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        solver = SudokuSolver(board)
        self.assertEqual(solver.count_solutions(limit=5), 1)
        # count_solutions must not mutate the original board.
        self.assertFalse(board.is_full())

    def test_count_solutions_already_solved(self) -> None:
        board = SudokuBoard(SOLVED_PUZZLE)
        solver = SudokuSolver(board)
        self.assertEqual(solver.count_solutions(limit=5), 1)

    def test_get_hint_returns_correct_value(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        solver = SudokuSolver(board)
        hint = solver.get_hint()
        self.assertIsNotNone(hint)
        row, col, value = hint  # type: ignore[misc]
        self.assertEqual((row, col), (0, 2))
        self.assertEqual(value, 4)
        # get_hint must not mutate the original board.
        self.assertEqual(board.get(0, 2), 0)

    def test_get_hint_on_full_board_returns_none(self) -> None:
        board = SudokuBoard(SOLVED_PUZZLE)
        solver = SudokuSolver(board)
        self.assertIsNone(solver.get_hint())

    def test_solve_steps_reaches_solution(self) -> None:
        board = SudokuBoard(EASY_PUZZLE)
        solver = SudokuSolver(board)
        for _ in solver.solve_steps():
            pass
        self.assertTrue(_is_full_and_valid(board))


class TestUtils(unittest.TestCase):
    """Tests for the generator and difficulty-estimation utilities."""

    def test_generate_puzzle_has_unique_solution(self) -> None:
        board = generate_puzzle(clues=40, seed=42)
        solver = SudokuSolver(board)
        self.assertEqual(solver.count_solutions(limit=2), 1)

    def test_generate_puzzle_rejects_out_of_range_clues(self) -> None:
        with self.assertRaises(ValueError):
            generate_puzzle(clues=10)

    def test_estimate_difficulty_labels(self) -> None:
        easy_board = SudokuBoard(EASY_PUZZLE)
        self.assertIn(
            estimate_difficulty(easy_board), {"Easy", "Medium", "Hard", "Very Hard"}
        )


if __name__ == "__main__":
    unittest.main()
