"""
solver.py

Implements the SudokuSolver class: a recursive backtracking engine
that solves 9x9 Sudoku puzzles, plus supporting features such as
solution counting, hint generation, and step-by-step solving.

Algorithm overview (backtracking)
----------------------------------
Backtracking is a depth-first search over the space of possible cell
assignments. At each step we:

  1. Find the next empty cell. The base case is that there is none
     left, meaning the board is completely and validly filled, i.e.
     solved.
  2. Try each candidate digit 1-9 that does not currently conflict with
     its row, column, or 3x3 box.
  3. Recurse into the rest of the board using this tentative
     assignment.
  4. If the recursive call fails to complete the puzzle, undo
     ("backtrack") the assignment and try the next candidate digit.
  5. If no candidate digit works for this cell, return False, which
     causes the *caller* (the previous recursive call) to backtrack
     as well.

Why recursion works: each recursive call only ever has to solve a
strictly smaller sub-problem (the board with one fewer empty cell), so
the recursion is guaranteed to terminate, and correctness follows by
induction on the number of empty cells - solving a board with 0 empty
cells is trivially correct (it's already solved), and solving a board
with k empty cells reduces to placing one valid, non-conflicting digit
and then solving the remaining k-1 empty cells.

Time complexity: in the worst case, backtracking is O(9^m), where m is
the number of empty cells, since each empty cell may need to try up to
9 digits before the correct one is found. In practice, the row/column/
box constraints prune the vast majority of branches almost
immediately, so real 9x9 puzzles typically solve in a few milliseconds.

Space complexity: O(m) for the recursion call stack (m <= 81), plus
O(1) additional bookkeeping per call.
"""

from __future__ import annotations

from typing import Generator, List, Optional, Tuple

from board import SudokuBoard
from utils import BOX_SIZE, EMPTY_CELL, GRID_SIZE


class SudokuSolver:
    """Solves a SudokuBoard in place using recursive backtracking."""

    def __init__(self, board: SudokuBoard) -> None:
        """Create a solver bound to a specific board.

        Args:
            board: The SudokuBoard instance to solve. It is modified
                in place by solve() and solve_steps().
        """
        self.board = board

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------
    def find_empty(self) -> Optional[Tuple[int, int]]:
        """Find the next empty cell, scanning row by row.

        Returns:
            A (row, col) tuple for the first empty cell found, or None
            if the board is completely filled.
        """
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.board.get(row, col) == EMPTY_CELL:
                    return row, col
        return None

    def is_valid(self, row: int, col: int, num: int) -> bool:
        """Check whether placing num at (row, col) breaks no rule.

        Args:
            row: Zero-based row index.
            col: Zero-based column index.
            num: Candidate digit (1-9).

        Returns:
            True if num does not already appear in the same row,
            column, or 3x3 box.
        """
        grid = self.board.grid

        for c in range(GRID_SIZE):
            if grid[row][c] == num:
                return False

        for r in range(GRID_SIZE):
            if grid[r][col] == num:
                return False

        box_row = (row // BOX_SIZE) * BOX_SIZE
        box_col = (col // BOX_SIZE) * BOX_SIZE
        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if grid[r][c] == num:
                    return False

        return True

    # ------------------------------------------------------------------
    # Solving
    # ------------------------------------------------------------------
    def solve(self) -> bool:
        """Solve the board in place using recursive backtracking.

        Returns:
            True if a solution was found (self.board now holds it),
            False if the puzzle is unsolvable.
        """
        empty = self.find_empty()
        if empty is None:
            return True  # Base case: no empty cells left, puzzle solved.

        row, col = empty
        for num in range(1, 10):
            if self.is_valid(row, col, num):
                self.board.set(row, col, num)

                if self.solve():
                    return True

                self.board.set(row, col, EMPTY_CELL)  # Backtrack.

        return False  # No digit works here; trigger backtracking above.

    def solve_steps(self) -> Generator[Tuple[List[List[int]], str], None, bool]:
        """Solve the board like solve(), yielding a snapshot after each move.

        This generator-based variant is intended for visualizing or
        logging the algorithm's progress step by step. Each yielded
        item is a (grid_snapshot, action) pair, where action describes
        either a tentative placement or a backtrack.

        Yields:
            Tuples of (deep-copied grid, human-readable description).

        Returns:
            True if solved, False otherwise (available as the
            generator's StopIteration.value, or simply reflected in
            the final state of self.board).
        """
        empty = self.find_empty()
        if empty is None:
            return True

        row, col = empty
        for num in range(1, 10):
            if self.is_valid(row, col, num):
                self.board.set(row, col, num)
                yield self.board.to_list(), f"place {num} at ({row}, {col})"

                solved = yield from self.solve_steps()
                if solved:
                    return True

                self.board.set(row, col, EMPTY_CELL)
                yield self.board.to_list(), f"backtrack from ({row}, {col})"

        return False

    def count_solutions(self, limit: int = 2) -> int:
        """Count how many distinct solutions the board has, up to a limit.

        This is used both to check puzzle uniqueness (limit=2 is
        enough to distinguish "exactly one" from "more than one") and,
        with a larger limit, to get a capped count for small or
        heavily under-constrained puzzles.

        The board bound to this solver is never modified; counting is
        performed on an internal copy.

        Args:
            limit: Stop counting once this many solutions are found,
                to avoid wasted work on puzzles with many solutions.

        Returns:
            The number of solutions found, capped at `limit`.
        """
        working_solver = SudokuSolver(self.board.copy())
        return working_solver._count_solutions_recursive(limit)

    def _count_solutions_recursive(self, limit: int) -> int:
        """Recursive helper for count_solutions; mutates self.board directly."""
        empty = self.find_empty()
        if empty is None:
            return 1

        row, col = empty
        total = 0
        for num in range(1, 10):
            if self.is_valid(row, col, num):
                self.board.set(row, col, num)
                total += self._count_solutions_recursive(limit - total)
                self.board.set(row, col, EMPTY_CELL)
                if total >= limit:
                    break
        return total

    # ------------------------------------------------------------------
    # Hints
    # ------------------------------------------------------------------
    def get_hint(self) -> Optional[Tuple[int, int, int]]:
        """Suggest a single correct next move without altering the board.

        Internally solves a full copy of the board and reports what
        value belongs in the first empty cell, leaving the solver's
        actual board untouched.

        Returns:
            A (row, col, value) tuple giving one correct placement, or
            None if the board is already full or has no solution.
        """
        empty = self.find_empty()
        if empty is None:
            return None

        working_board = self.board.copy()
        working_solver = SudokuSolver(working_board)
        if not working_solver.solve():
            return None

        row, col = empty
        return row, col, working_board.get(row, col)
