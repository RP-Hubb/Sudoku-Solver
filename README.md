# Sudoku Solver

A clean, well-tested, object-oriented Sudoku solver written in pure Python
(standard library only) that uses **recursive backtracking** to solve any
valid 9×9 Sudoku puzzle. Includes a command-line interface, a puzzle
generator, a hint system, a step-by-step solving trace, and a full
`unittest` suite.

```
5 3 . | . 7 . | . . .        5 3 4 | 6 7 8 | 9 1 2
6 . . | 1 9 5 | . . .        6 7 2 | 1 9 5 | 3 4 8
. 9 8 | . . . | . 6 .        1 9 8 | 3 4 2 | 5 6 7
------+-------+------  -->   ------+-------+------
8 . . | . 6 . | . . 3        8 5 9 | 7 6 1 | 4 2 3
4 . . | 8 . 3 | . . 1        4 2 6 | 8 5 3 | 7 9 1
7 . . | . 2 . | . . 6        7 1 3 | 9 2 4 | 8 5 6
------+-------+------        ------+-------+------
. 6 . | . . . | 2 8 .        9 6 1 | 5 3 7 | 2 8 4
. . . | 4 1 9 | . . 5        2 8 7 | 4 1 9 | 6 3 5
. . . | . 8 . | . 7 9        3 4 5 | 2 8 6 | 1 7 9
```

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Algorithm Explanation](#algorithm-explanation)
- [Complexity Analysis](#complexity-analysis)
- [Installation](#installation)
- [Usage](#usage)
- [Example Output](#example-output)
- [Running the Tests](#running-the-tests)
- [Code Quality](#code-quality)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview

This project implements a Sudoku solver from first principles, without
relying on any third-party Sudoku or constraint-solving libraries. It is
organized as a small set of focused modules — a board representation, a
solver, shared utilities, and a CLI — so that each piece can be read,
tested, and reused independently.

It was built to be **portfolio-ready**: fully documented, type-hinted,
PEP 8 compliant, covered by unit tests, and runnable immediately after
cloning with no setup beyond a standard Python 3.12+ installation.

## Features

- **9×9 board representation** (`board.py`) with clean grid printing,
  loading from a Python list or a text file, and saving to a text file.
- **Recursive backtracking solver** (`solver.py`) with `find_empty()`,
  `is_valid()`, and `solve()`, exactly as specified by the classic
  backtracking approach to Sudoku.
- **Input validation** that checks board dimensions, value ranges, and
  Sudoku's row/column/box rules, raising descriptive custom exceptions.
- **Pretty printing** of both the original and solved puzzle, with `|`
  and `-` separators between 3×3 blocks.
- **Five example puzzles** (`examples.py`): easy, medium, hard, a
  nearly-completed puzzle, an already-solved puzzle, and an intentionally
  invalid puzzle.
- **A `unittest` suite** (`test_solver.py`) with 29 tests covering
  validation, placement rules, solving at every difficulty level,
  invalid-board detection, solution counting, and hints.
- **Bonus features**:
  - Counting the number of solutions a puzzle has (`count_solutions`).
  - A single-move hint generator (`get_hint`).
  - A step-by-step solving trace (`solve_steps`) for visualizing the
    algorithm.
  - A random puzzle generator that guarantees a unique solution
    (`generate_puzzle`).
  - A simple clue-count-based difficulty estimator
    (`estimate_difficulty`).
  - A full command-line interface (`main.py`) built with `argparse`.
  - Solving puzzles loaded from a text file, and exporting solutions to
    a text file.

## Project Structure

```
sudoku-solver/
│
├── main.py          # Command-line interface (argparse)
├── solver.py         # SudokuSolver: backtracking, hints, counting
├── board.py          # SudokuBoard: representation, validation, I/O
├── utils.py           # Constants, exceptions, generator, difficulty
├── examples.py         # Example puzzles (easy/medium/hard/etc.)
├── test_solver.py       # unittest suite
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

Each module has a single, clear responsibility:

| Module          | Responsibility                                              |
|-----------------|---------------------------------------------------------------|
| `board.py`      | Data + validation + display + file I/O for a Sudoku grid.    |
| `solver.py`     | The backtracking algorithm and its variants (hints, counting, step tracing). |
| `utils.py`      | Shared constants, exception types, puzzle generation, difficulty estimation. |
| `examples.py`   | Static example puzzles used by the CLI and the tests.        |
| `main.py`       | Ties everything together behind a command-line interface.    |
| `test_solver.py`| Automated correctness checks for every module above.         |

## Algorithm Explanation

The solver uses **recursive backtracking**, a form of depth-first search
over the space of possible digit assignments:

1. **Find an empty cell.** `find_empty()` scans the board row by row and
   returns the coordinates of the first cell that still holds `0`.
2. **Base case.** If `find_empty()` finds nothing, every cell is filled
   and — because every digit placed so far was checked against the
   rules on the way in — the board is a valid, complete solution.
   `solve()` returns `True` immediately.
3. **Try candidates.** For the empty cell found, the algorithm tries each
   digit `1`–`9` in turn. `is_valid()` checks that the digit does not
   already appear in the same row, column, or 3×3 box.
4. **Recurse.** If a digit is valid, it is tentatively placed, and
   `solve()` calls itself to solve the rest of the board.
5. **Backtrack.** If that recursive call ultimately fails (returns
   `False`), the digit is undone (reset to `0`) and the next candidate
   digit is tried. If no digit from `1`–`9` works for the current cell,
   the function returns `False`, which causes the *previous* call in the
   recursion to backtrack in turn.

### Why recursion works

Each recursive call only ever needs to solve a **strictly smaller**
sub-problem: the same board, but with one fewer empty cell. Because the
number of empty cells decreases by exactly one on every successful
placement and can never go negative, the recursion is guaranteed to
terminate. Correctness follows by induction on the number of empty
cells:

- **Base case (0 empty cells):** the board is already fully and validly
  filled, so it is trivially a correct solution.
- **Inductive step (k empty cells):** solving the board reduces to
  finding one digit that is locally valid for one empty cell, and then
  solving the remaining board, which has `k - 1` empty cells and is
  solved correctly by the inductive hypothesis.

### The backtracking step, precisely

Backtracking is what makes this exhaustive search tractable to describe:
whenever a branch of the search cannot lead to a solution (no digit
works, or every digit was tried and every resulting sub-problem failed),
the algorithm **undoes** its last decision and returns control to the
caller, which then tries a different decision. This is exactly the
`self.board.set(row, col, EMPTY_CELL)` line that runs after a recursive
`solve()` call returns `False` in `solver.py`.

## Complexity Analysis

**Time complexity:** In the worst case, each of the `m` empty cells can
require trying up to 9 candidate digits, giving a worst-case bound of
**O(9^m)**, where `m` is the number of empty cells (at most 81). In
practice, the row/column/box constraint checks in `is_valid()` prune
the vast majority of the search tree almost immediately, so real 9×9
puzzles — even ones with very few given clues — typically solve in
single-digit to low-hundreds of milliseconds on ordinary hardware.

**Space complexity:** The recursion depth is bounded by the number of
empty cells (`m ≤ 81`), and each stack frame does O(1) additional work,
so the algorithm uses **O(m)** space for the call stack, plus the O(1)
fixed-size 9×9 board itself.

## Installation

Requires **Python 3.12+**. No third-party packages are needed to run the
solver itself.

```bash
git clone https://github.com/<your-username>/sudoku-solver.git
cd sudoku-solver
python3 main.py --puzzle easy
```

That's it — there is nothing to `pip install` for normal use. `requirements.txt`
only lists optional developer tools (linting/type-checking).

## Usage

The CLI is built with `argparse` and exposes every core feature:

```bash
# Solve one of the built-in example puzzles
python main.py --puzzle easy
python main.py --puzzle medium
python main.py --puzzle hard

# Solve a puzzle from a text file, and save the solution to another file
python main.py --file my_puzzle.txt --output solved.txt

# Get a single hint instead of solving the whole board
python main.py --puzzle easy --hint

# Watch a step-by-step trace of the backtracking process
python main.py --puzzle easy --steps --max-steps 10

# Count how many solutions a puzzle has (useful for checking uniqueness)
python main.py --puzzle medium --count-solutions

# Generate a brand-new, uniquely-solvable puzzle
python main.py --generate 32 --seed 7

# Estimate a puzzle's difficulty
python main.py --puzzle hard --difficulty
```

Run `python main.py --help` to see the full list of options.

### Puzzle file format

Text files should contain 9 non-blank lines, each either 9 characters
long or 9 whitespace-separated tokens, using `0` or `.` for empty cells:

```
53..7....
6..195...
.98....6.
8...6...3
4..8.3..1
7...2...6
.6....28.
...419..5
....8..79
```

### Using the library directly

```python
from board import SudokuBoard
from solver import SudokuSolver
from examples import EASY_PUZZLE

board = SudokuBoard(EASY_PUZZLE)
solver = SudokuSolver(board)

if solver.solve():
    print(board)
else:
    print("No solution exists.")
```

## Example Output

```text
$ python main.py --puzzle easy
Puzzle:
5 3 . | . 7 . | . . .
6 . . | 1 9 5 | . . .
. 9 8 | . . . | . 6 .
------+-------+------
8 . . | . 6 . | . . 3
4 . . | 8 . 3 | . . 1
7 . . | . 2 . | . . 6
------+-------+------
. 6 . | . . . | 2 8 .
. . . | 4 1 9 | . . 5
. . . | . 8 . | . 7 9

Solved puzzle:
5 3 4 | 6 7 8 | 9 1 2
6 7 2 | 1 9 5 | 3 4 8
1 9 8 | 3 4 2 | 5 6 7
------+-------+------
8 5 9 | 7 6 1 | 4 2 3
4 2 6 | 8 5 3 | 7 9 1
7 1 3 | 9 2 4 | 8 5 6
------+-------+------
9 6 1 | 5 3 7 | 2 8 4
2 8 7 | 4 1 9 | 6 3 5
3 4 5 | 2 8 6 | 1 7 9

Solved in 27.27 ms.
```

```text
$ python main.py --puzzle easy --hint
Hint: place 4 at row 1, column 3.
```

```text
$ python main.py --puzzle easy --count-solutions
Number of solutions found (capped at 10): 1
```

```text
$ python main.py --puzzle invalid
Error: Duplicate value 5 conflicts at row 0, column 0.
```

## Running the Tests

The project ships with a comprehensive `unittest` suite (29 tests) with
no external test dependencies:

```bash
python -m unittest test_solver.py -v
```

Expected output ends with:

```
----------------------------------------------------------------------
Ran 29 tests in 0.7s

OK
```

Tests cover:

- Board construction and validation (dimensions, value ranges, rule
  conflicts, `is_full`, copying, string rendering).
- `find_empty()` and `is_valid()` in isolation, including row, column,
  and box conflicts.
- Full solving of the easy, medium, and hard example puzzles.
- Solving a nearly-completed puzzle and an already-solved puzzle.
- Detection of an invalid initial board via a raised exception.
- Solution counting, hint generation, and the step-by-step generator.
- The puzzle generator and difficulty estimator.

## Code Quality

- **Type hints** on every function and method signature.
- **Docstrings** (Google-style) on every public class, method, and
  function, explaining purpose, arguments, return values, and raised
  exceptions.
- **PEP 8 compliant**: verified with `flake8` (zero warnings).
- **Statically type-checked**: verified with `mypy --strict`-adjacent
  settings (zero errors).
- **No duplicated logic**: the row/column/box conflict check exists in
  exactly one place relevant to each concern (`SudokuBoard` uses it for
  initial validation; `SudokuSolver.is_valid()` is the single source of
  truth used throughout solving, counting, and hinting).
- **Modular design**: board representation, solving logic, shared
  utilities, example data, and the CLI are all cleanly separated.

## Future Improvements

Ideas for extending this project further:

- **Constraint propagation** (e.g. naked singles, hidden singles,
  pointing pairs) layered on top of backtracking to solve most puzzles
  without any guessing, and to produce more human-like difficulty
  ratings.
- **A graphical interface** (e.g. with `tkinter` or a small web front
  end) that visualizes the backtracking trace produced by
  `solve_steps()` in real time.
- **Support for larger variants**, such as 16×16 Sudoku or Sudoku with
  additional regions (e.g. diagonals in "X-Sudoku").
- **Parallelized solution counting** for exhaustively analyzing puzzles
  with many solutions.
- **A proper difficulty estimator** based on which human solving
  techniques are required, rather than simply counting clues.
- **Packaging** the project for `pip install` with a console-script
  entry point.

## License

This project is released under the [MIT License](LICENSE).
