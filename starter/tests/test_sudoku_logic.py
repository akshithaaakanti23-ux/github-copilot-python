import copy

import pytest

import sudoku_logic


def assert_valid_solution(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    for start_row in range(0, sudoku_logic.SIZE, 3):
        for start_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                board[row][col]
                for row in range(start_row, start_row + 3)
                for col in range(start_col, start_col + 3)
            }
            assert box == expected


def test_create_empty_board_has_nine_rows_of_empty_cells():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(cell == sudoku_logic.EMPTY for row in board for cell in row)


def test_deep_copy_is_independent_of_original_board():
    board = sudoku_logic.create_empty_board()

    copied_board = sudoku_logic.deep_copy(board)
    copied_board[0][0] = 7

    assert board[0][0] == sudoku_logic.EMPTY
    assert copied_board[0][0] == 7


@pytest.mark.parametrize(
    ("row", "col", "number", "is_expected_safe"),
    [
        (0, 1, 5, False),
        (1, 0, 5, False),
        (1, 1, 5, False),
        (4, 4, 5, True),
    ],
)
def test_is_safe_checks_row_column_and_box(
    row, col, number, is_expected_safe
):
    board = sudoku_logic.create_empty_board()
    board[0][0] = 5

    assert sudoku_logic.is_safe(board, row, col, number) is is_expected_safe


def test_fill_board_completes_a_valid_sudoku_solution():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board) is True
    assert_valid_solution(board)


@pytest.mark.parametrize("clue_count", [30, 35, 45, 81])
def test_remove_cells_leaves_the_requested_number_of_clues(clue_count):
    board = sudoku_logic.create_empty_board()
    assert sudoku_logic.fill_board(board) is True

    sudoku_logic.remove_cells(board, clue_count)

    assert sum(cell != sudoku_logic.EMPTY for row in board for cell in row) == (
        clue_count
    )


def test_remove_cells_does_not_change_values_that_remain():
    board = sudoku_logic.create_empty_board()
    assert sudoku_logic.fill_board(board) is True
    original = copy.deepcopy(board)

    sudoku_logic.remove_cells(board, 35)

    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if board[row][col] != sudoku_logic.EMPTY:
                assert board[row][col] == original[row][col]


def test_generate_puzzle_returns_requested_clues_and_matching_solution():
    clue_count = 35

    puzzle, solution = sudoku_logic.generate_puzzle(clue_count)

    assert_valid_solution(solution)
    assert sudoku_logic.is_valid_board(puzzle)
    assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == (
        clue_count
    )
    assert sudoku_logic.count_solutions(puzzle) == 1
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if puzzle[row][col] != sudoku_logic.EMPTY:
                assert puzzle[row][col] == solution[row][col]


def test_generate_puzzle_uses_35_clues_by_default():
    puzzle, solution = sudoku_logic.generate_puzzle()

    assert_valid_solution(solution)
    assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == 35
    assert sudoku_logic.count_solutions(puzzle) == 1


def test_solution_counter_stops_at_requested_limit():
    assert sudoku_logic.count_solutions(
        sudoku_logic.create_empty_board(), limit=2
    ) == 2


@pytest.mark.parametrize(
    ("difficulty", "clue_range"),
    [
        ("easy", sudoku_logic.DIFFICULTY_CLUE_RANGES["easy"]),
        ("medium", sudoku_logic.DIFFICULTY_CLUE_RANGES["medium"]),
        ("hard", sudoku_logic.DIFFICULTY_CLUE_RANGES["hard"]),
    ],
)
def test_generated_difficulty_puzzles_are_valid_and_unique(
    difficulty, clue_range
):
    puzzle, solution = sudoku_logic.generate_puzzle(difficulty=difficulty)
    clue_count = sum(
        value != sudoku_logic.EMPTY for row in puzzle for value in row
    )

    assert_valid_solution(solution)
    assert sudoku_logic.is_valid_board(puzzle)
    assert clue_range[0] <= clue_count <= clue_range[1]
    assert sudoku_logic.count_solutions(puzzle) == 1
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if puzzle[row][col] != sudoku_logic.EMPTY:
                assert puzzle[row][col] == solution[row][col]


def test_solution_counter_returns_zero_for_invalid_board():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 1
    board[0][1] = 1

    assert sudoku_logic.count_solutions(board) == 0


@pytest.mark.parametrize("clue_count", [16, 82])
def test_generate_puzzle_rejects_out_of_range_clue_counts(clue_count):
    with pytest.raises(ValueError, match="clues must be between"):
        sudoku_logic.generate_puzzle(clues=clue_count)


def test_generate_puzzle_rejects_unknown_difficulty():
    with pytest.raises(ValueError, match="difficulty must be one of"):
        sudoku_logic.generate_puzzle(difficulty="expert")
