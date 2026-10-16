import pytest

import app as sudoku_app
import sudoku_logic


@pytest.fixture
def client():
    sudoku_app.GAME_STATES.clear()
    sudoku_app.app.config["TESTING"] = True

    with sudoku_app.app.test_client() as test_client:
        yield test_client

    sudoku_app.GAME_STATES.clear()


def get_game_state(client):
    with client.session_transaction() as current_session:
        game_id = current_session["game_id"]
    return sudoku_app.GAME_STATES[game_id]


def test_index_route_renders_game_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_new_route_returns_puzzle_and_keeps_solution_server_side(client):
    response = client.get("/new?clues=35")
    data = response.get_json()

    assert response.status_code == 200
    assert data is not None
    assert set(data) == {"puzzle"}
    assert len(data["puzzle"]) == sudoku_logic.SIZE
    assert sum(
        cell != sudoku_logic.EMPTY
        for row in data["puzzle"]
        for cell in row
    ) == 35
    assert get_game_state(client)["solution"] is not None


@pytest.mark.parametrize(
    ("difficulty", "clue_range"),
    [
        ("easy", sudoku_logic.DIFFICULTY_CLUE_RANGES["easy"]),
        ("medium", sudoku_logic.DIFFICULTY_CLUE_RANGES["medium"]),
        ("hard", sudoku_logic.DIFFICULTY_CLUE_RANGES["hard"]),
    ],
)
def test_new_route_generates_requested_difficulty(
    client, difficulty, clue_range
):
    response = client.get(f"/new?difficulty={difficulty}")
    data = response.get_json()
    puzzle = data["puzzle"]
    clue_count = sum(
        cell != sudoku_logic.EMPTY for row in puzzle for cell in row
    )

    assert response.status_code == 200
    assert set(data) == {"puzzle"}
    assert clue_range[0] <= clue_count <= clue_range[1]
    assert sudoku_logic.is_valid_board(puzzle)
    assert sudoku_logic.count_solutions(puzzle) == 1


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("difficulty=expert", "difficulty must be one of"),
        ("clues=not-a-number", "clues must be an integer"),
        ("clues=16", "clues must be between"),
    ],
)
def test_new_route_returns_a_client_error_for_invalid_parameters(
    client, query, message
):
    response = client.get(f"/new?{query}")

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_check_route_returns_error_when_no_game_is_in_progress(client):
    response = client.post("/check", json={"board": sudoku_logic.create_empty_board()})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_route_accepts_a_correct_solution(client):
    new_game = client.get("/new?clues=35")
    solution = get_game_state(client)["solution"]

    response = client.post("/check", json={"board": solution})

    assert new_game.status_code == 200
    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "complete": True,
        "hints_used": 0,
    }


def test_check_route_returns_hint_count_when_puzzle_is_completed(client):
    client.get("/new?clues=35")
    state = get_game_state(client)
    board = [row.copy() for row in state["puzzle"]]
    hint = client.post("/hint", json={"board": board}).get_json()
    board[hint["row"]][hint["col"]] = hint["value"]
    solution = state["solution"]

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "complete": True,
        "hints_used": 1,
    }


def test_check_route_returns_coordinates_of_incorrect_cells(client):
    new_game = client.get("/new?clues=35")
    state = get_game_state(client)
    solution = state["solution"]
    submitted_board = [row.copy() for row in solution]
    row, col = next(
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if state["puzzle"][row][col] == sudoku_logic.EMPTY
    )
    submitted_board[row][col] = solution[row][col] % sudoku_logic.SIZE + 1

    response = client.post("/check", json={"board": submitted_board})

    assert new_game.status_code == 200
    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [[row, col]],
        "complete": False,
        "hints_used": 0,
    }


def test_check_does_not_report_empty_cells_as_incorrect_or_complete(client):
    client.get("/new?clues=35")
    puzzle = get_game_state(client)["puzzle"]

    response = client.post("/check", json={"board": puzzle})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "complete": False,
        "hints_used": 0,
    }


def test_check_rejects_changes_to_original_clues(client):
    client.get("/new?clues=35")
    state = get_game_state(client)
    board = [row.copy() for row in state["puzzle"]]
    row, col = next(
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if state["puzzle"][row][col] != sudoku_logic.EMPTY
    )
    board[row][col] = board[row][col] % sudoku_logic.SIZE + 1

    response = client.post("/check", json={"board": board})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Original clues and hinted cells cannot be changed"
    }


@pytest.mark.parametrize(
    "board",
    [
        None,
        [],
        [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
        [[False] + [0] * (sudoku_logic.SIZE - 1)]
        + [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
        [[10] + [0] * (sudoku_logic.SIZE - 1)]
        + [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
    ],
)
def test_check_rejects_malformed_boards(client, board):
    client.get("/new?clues=35")

    response = client.post("/check", json={"board": board})

    assert response.status_code == 400
    assert "board must be a 9x9 grid" in response.get_json()["error"]


def test_hint_fills_one_empty_cell_and_returns_only_that_value(client):
    client.get("/new?clues=35")
    state = get_game_state(client)
    board = [row.copy() for row in state["puzzle"]]
    empty_count = sum(value == 0 for row in board for value in row)

    response = client.post("/hint", json={"board": board})
    data = response.get_json()
    row, col = data["row"], data["col"]

    assert response.status_code == 200
    assert data == {
        "row": row,
        "col": col,
        "value": state["solution"][row][col],
        "hints_used": 1,
    }
    assert board[row][col] == 0
    assert len(data) == 4
    board[row][col] = data["value"]
    assert sum(value == 0 for row in board for value in row) == empty_count - 1


def test_hint_locks_filled_cell_and_increments_hint_count(client):
    client.get("/new?clues=35")
    state = get_game_state(client)
    board = [row.copy() for row in state["puzzle"]]

    first_hint = client.post("/hint", json={"board": board}).get_json()
    board[first_hint["row"]][first_hint["col"]] = first_hint["value"]
    second_hint_response = client.post("/hint", json={"board": board})
    second_hint = second_hint_response.get_json()

    assert second_hint_response.status_code == 200
    assert second_hint["hints_used"] == 2
    assert (second_hint["row"], second_hint["col"]) != (
        first_hint["row"],
        first_hint["col"],
    )
    board[first_hint["row"]][first_hint["col"]] = (
        first_hint["value"] % sudoku_logic.SIZE + 1
    )
    tampered_hint = client.post("/check", json={"board": board})
    assert tampered_hint.status_code == 400


def test_hint_returns_error_when_no_game_or_no_empty_cells(client):
    response_without_game = client.post(
        "/hint", json={"board": sudoku_logic.create_empty_board()}
    )
    assert response_without_game.status_code == 400

    client.get("/new?clues=81")
    response_without_empty_cells = client.post(
        "/hint", json={"board": get_game_state(client)["puzzle"]}
    )

    assert response_without_empty_cells.status_code == 400
    assert response_without_empty_cells.get_json() == {
        "error": "There are no empty cells to fill"
    }


def test_game_state_is_isolated_between_clients(client):
    other_client = sudoku_app.app.test_client()
    client.get("/new?clues=35")

    response = other_client.post(
        "/check", json={"board": sudoku_logic.create_empty_board()}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_game_page_includes_difficulty_hint_and_check_controls(client):
    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="difficulty"' in page
    assert 'id="get-hint"' in page
    assert 'id="check-solution"' in page
    assert 'id="timer"' in page
    assert 'id="score-entry-form"' in page
    assert 'id="leaderboard-entries"' in page
    assert all(
        heading in page
        for heading in (
            "Rank",
            "Player Name",
            "Time",
            "Difficulty",
            "Hints Used",
        )
    )


def test_game_page_includes_accessible_theme_and_board_controls(client):
    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<html lang="en">' in page
    assert 'id="theme-toggle"' in page
    assert 'aria-label="Switch to dark mode"' in page
    assert 'aria-pressed="false"' in page
    assert 'id="sudoku-board" role="grid" aria-label="Sudoku puzzle"' in page


def test_stylesheet_supports_dark_theme_and_sudoku_cell_states(client):
    response = client.get("/static/styles.css")
    stylesheet = response.get_data(as_text=True)

    assert response.status_code == 200
    assert ':root[data-theme="dark"]' in stylesheet
    assert ".sudoku-cell.box-shade-a" in stylesheet
    assert ".sudoku-cell.box-shade-b" in stylesheet
    assert ".sudoku-cell.prefilled" in stylesheet
    assert ".sudoku-cell.hinted" in stylesheet
    assert ".sudoku-cell.incorrect" in stylesheet
    assert ".sudoku-cell.conflict" in stylesheet
