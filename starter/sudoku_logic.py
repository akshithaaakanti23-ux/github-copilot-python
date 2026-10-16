"""Sudoku board creation, validation, solving, and puzzle generation."""

import copy
import random

SIZE = 9
EMPTY = 0
Board = list[list[int]]

# Clue bands are inclusive and intentionally non-overlapping.
DIFFICULTY_CLUE_RANGES = {
    "easy": (40, 45),
    "medium": (33, 39),
    "hard": (28, 32),
}
MINIMUM_CLUES = 17
GENERATION_ATTEMPTS = 20


def deep_copy(board: Board) -> Board:
    """Return a recursive copy of a Sudoku board."""
    return copy.deepcopy(board)


def create_empty_board() -> Board:
    """Create a 9x9 board containing only empty cells."""
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_safe(board: Board, row: int, col: int, num: int) -> bool:
    """Return whether num can be placed at row and col."""
    for index in range(SIZE):
        if board[row][index] == num or board[index][col] == num:
            return False

    start_row = row - row % 3
    start_col = col - col % 3
    for box_row in range(start_row, start_row + 3):
        for box_col in range(start_col, start_col + 3):
            if board[box_row][box_col] == num:
                return False
    return True


def is_valid_board(board: Board) -> bool:
    """Return whether a board has valid dimensions, values, and Sudoku units."""
    if not isinstance(board, list) or len(board) != SIZE:
        return False
    if any(not isinstance(row, list) or len(row) != SIZE for row in board):
        return False
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < EMPTY
        or value > SIZE
        for row in board
        for value in row
    ):
        return False

    units = list(board)
    units.extend(
        [[board[row][col] for row in range(SIZE)] for col in range(SIZE)]
    )
    for start_row in range(0, SIZE, 3):
        for start_col in range(0, SIZE, 3):
            units.append(
                [
                    board[row][col]
                    for row in range(start_row, start_row + 3)
                    for col in range(start_col, start_col + 3)
                ]
            )

    for unit in units:
        values = [value for value in unit if value != EMPTY]
        if len(values) != len(set(values)):
            return False
    return True


def fill_board(board: Board) -> bool:
    """Fill empty cells with a randomized valid Sudoku solution."""
    if not is_valid_board(board):
        return False

    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                candidates = list(range(1, SIZE + 1))
                random.shuffle(candidates)
                for candidate in candidates:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def count_solutions(board: Board, limit: int = 2) -> int:
    """Count solutions, stopping as soon as limit solutions are found."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not is_valid_board(board):
        return 0

    working_board = deep_copy(board)
    solution_count = 0

    def search() -> None:
        nonlocal solution_count
        if solution_count >= limit:
            return

        best_cell = None
        best_candidates = None
        for row in range(SIZE):
            for col in range(SIZE):
                if working_board[row][col] != EMPTY:
                    continue
                candidates = [
                    number
                    for number in range(1, SIZE + 1)
                    if is_safe(working_board, row, col, number)
                ]
                if not candidates:
                    return
                if best_candidates is None or len(candidates) < len(
                    best_candidates
                ):
                    best_cell = (row, col)
                    best_candidates = candidates
                    if len(best_candidates) == 1:
                        break
            if best_candidates is not None and len(best_candidates) == 1:
                break

        if best_cell is None:
            solution_count += 1
            return

        assert best_candidates is not None
        row, col = best_cell
        for candidate in best_candidates:
            working_board[row][col] = candidate
            search()
            working_board[row][col] = EMPTY
            if solution_count >= limit:
                return

    search()
    return solution_count


def remove_cells(board: Board, clues: int) -> None:
    """Remove random filled cells until exactly clues cells remain."""
    if not isinstance(clues, int) or isinstance(clues, bool):
        raise ValueError("clues must be an integer")
    if clues < 0 or clues > SIZE * SIZE:
        raise ValueError(f"clues must be between 0 and {SIZE * SIZE}")

    filled_cells = [
        (row, col)
        for row in range(SIZE)
        for col in range(SIZE)
        if board[row][col] != EMPTY
    ]
    if clues > len(filled_cells):
        raise ValueError("clues cannot exceed the number of filled cells")
    for row, col in random.sample(filled_cells, len(filled_cells) - clues):
        board[row][col] = EMPTY


def _remove_cells_preserving_uniqueness(
    solution: Board, target_clues: int
) -> Board:
    """Remove clues while retaining exactly one solution."""
    puzzle = deep_copy(solution)
    cells = [(row, col) for row in range(SIZE) for col in range(SIZE)]
    random.shuffle(cells)

    remaining_clues = SIZE * SIZE
    for row, col in cells:
        if remaining_clues == target_clues:
            break
        value = puzzle[row][col]
        puzzle[row][col] = EMPTY
        if count_solutions(puzzle, limit=2) == 1:
            remaining_clues -= 1
        else:
            puzzle[row][col] = value
    return puzzle


def generate_puzzle(
    clues: int = 35, difficulty: str | None = None
) -> tuple[Board, Board]:
    """Generate a unique-solution puzzle with a requested clue count or level.

    Difficulty bands are Easy (40-45 clues), Medium (33-39), and Hard
    (28-32). When difficulty is specified, its band takes precedence over
    clues. Without difficulty, the legacy default of 35 clues is preserved.
    """
    clue_range = None
    if difficulty is not None:
        normalized_difficulty = difficulty.strip().lower()
        if normalized_difficulty not in DIFFICULTY_CLUE_RANGES:
            available = ", ".join(
                name.title() for name in DIFFICULTY_CLUE_RANGES
            )
            raise ValueError(f"difficulty must be one of: {available}")
        clue_range = DIFFICULTY_CLUE_RANGES[normalized_difficulty]
        target_clues = random.randint(*clue_range)
    else:
        if not isinstance(clues, int) or isinstance(clues, bool):
            raise ValueError("clues must be an integer")
        if not MINIMUM_CLUES <= clues <= SIZE * SIZE:
            raise ValueError(
                f"clues must be between {MINIMUM_CLUES} and {SIZE * SIZE}"
            )
        target_clues = clues

    best_puzzle = None
    for _ in range(GENERATION_ATTEMPTS):
        solution = create_empty_board()
        if not fill_board(solution):
            continue
        puzzle = _remove_cells_preserving_uniqueness(solution, target_clues)
        actual_clues = sum(
            value != EMPTY for row in puzzle for value in row
        )
        if clue_range is None and actual_clues == target_clues:
            return puzzle, solution
        if clue_range is not None and clue_range[0] <= actual_clues <= clue_range[1]:
            return puzzle, solution
        if best_puzzle is None or actual_clues < sum(
            value != EMPTY for row in best_puzzle[0] for value in row
        ):
            best_puzzle = puzzle, solution

    if best_puzzle is not None:
        best_clues = sum(
            value != EMPTY for row in best_puzzle[0] for value in row
        )
        if clue_range is not None and clue_range[0] <= best_clues <= clue_range[1]:
            return best_puzzle

    requested = (
        f"{difficulty.title()} difficulty ({clue_range[0]}-{clue_range[1]})"
        if clue_range is not None
        else f"{target_clues} clues"
    )
    raise RuntimeError(f"Could not generate a unique puzzle with {requested}")
