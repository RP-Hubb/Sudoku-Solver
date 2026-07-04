"""
main.py

Command-line interface for the Sudoku Solver project. Supports
solving example or file-based puzzles, generating new puzzles,
requesting a single hint, viewing a step-by-step solving trace,
counting solutions, estimating difficulty, and exporting results
to a file.

Examples:
    python main.py --puzzle hard
    python main.py --file my_puzzle.txt --output solved.txt
    python main.py --puzzle easy --hint
    python main.py --puzzle easy --steps
    python main.py --generate 32 --seed 7
    python main.py --puzzle medium --count-solutions
    python main.py --puzzle hard --difficulty
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import NoReturn

from board import SudokuBoard
from examples import EXAMPLES
from solver import SudokuSolver
from utils import SudokuError, estimate_difficulty, generate_puzzle


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sudoku-solver",
        description="Solve, analyze, and generate 9x9 Sudoku puzzles.",
    )

    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--puzzle",
        choices=sorted(EXAMPLES.keys()),
        help="Use one of the built-in example puzzles.",
    )
    source.add_argument(
        "--file",
        metavar="PATH",
        help="Load a puzzle from a text file (9 rows, '.' or '0' for empty).",
    )
    source.add_argument(
        "--generate",
        metavar="CLUES",
        type=int,
        help="Generate a random puzzle with roughly CLUES given cells.",
    )

    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for --generate."
    )
    parser.add_argument(
        "--output", metavar="PATH", help="Write the solved puzzle to this file."
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--hint", action="store_true", help="Show a single hint instead of solving."
    )
    mode.add_argument(
        "--steps",
        action="store_true",
        help="Print a step-by-step trace of the backtracking process.",
    )
    mode.add_argument(
        "--count-solutions",
        action="store_true",
        help="Report how many solutions the puzzle has instead of solving it.",
    )

    parser.add_argument(
        "--difficulty",
        action="store_true",
        help="Print an estimated difficulty rating for the puzzle.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=40,
        help="Maximum number of steps to print with --steps (default: 40).",
    )
    return parser


def load_board(args: argparse.Namespace) -> SudokuBoard:
    """Load a SudokuBoard according to the CLI arguments provided."""
    if args.file:
        return SudokuBoard.from_file(args.file)
    if args.generate is not None:
        return generate_puzzle(clues=args.generate, seed=args.seed)
    puzzle_name = args.puzzle or "easy"
    return SudokuBoard(EXAMPLES[puzzle_name])


def fail(message: str) -> NoReturn:
    """Print an error message to stderr and exit with a non-zero status."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def run(args: argparse.Namespace) -> None:
    """Execute the requested action based on parsed CLI arguments."""
    try:
        board = load_board(args)
    except SudokuError as exc:
        fail(str(exc))
        return
    except OSError as exc:
        fail(f"Could not read file: {exc}")
        return
    except ValueError as exc:
        fail(str(exc))
        return

    print("Puzzle:")
    print(board)
    print()

    if args.difficulty:
        print(f"Estimated difficulty: {estimate_difficulty(board)}")
        print()

    solver = SudokuSolver(board)

    if args.count_solutions:
        count = solver.count_solutions(limit=10)
        label = str(count) if count < 10 else "10 or more"
        print(f"Number of solutions found (capped at 10): {label}")
        return

    if args.hint:
        hint = solver.get_hint()
        if hint is None:
            print("No hint available (board is full or unsolvable).")
        else:
            row, col, value = hint
            print(f"Hint: place {value} at row {row + 1}, column {col + 1}.")
        return

    if args.steps:
        print("Step-by-step trace (backtracking):")
        step_count = 0
        for _, action in solver.solve_steps():
            if step_count < args.max_steps:
                print(f"  {step_count + 1:>5}: {action}")
            step_count += 1
        print(f"  ... {step_count} total steps.")
        print()
        print("Solved puzzle:")
        print(board)
        return

    start = time.perf_counter()
    solved = solver.solve()
    elapsed = time.perf_counter() - start

    if not solved:
        print("This puzzle has no solution.")
        return

    print("Solved puzzle:")
    print(board)
    print(f"\nSolved in {elapsed * 1000:.2f} ms.")

    if args.output:
        board.to_file(args.output)
        print(f"Solution written to {args.output}")


def main() -> None:
    """CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
