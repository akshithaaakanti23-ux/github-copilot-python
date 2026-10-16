# GitHub Copilot Evaluation:
# I evaluated the Copilot-assisted Sudoku implementation using automated
# pytest tests rather than relying only on the generated suggestions.
# I checked the unique-solution requirement and verified that the
# existing game functionality continued to pass the test suite.
# Final verification: 48 tests passed.
# Decision: Retained the implementation after successful verification.
"""Flask routes for the Sudoku game."""

import os
import random
import secrets
from typing import TypedDict

from flask import Flask, jsonify, render_template, request, session

import sudoku_logic

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)


class GameState(TypedDict):
    """Server-side state for one browser's active game."""

    puzzle: sudoku_logic.Board
    solution: sudoku_logic.Board
    hints: dict[tuple[int, int], int]


GAME_STATES: dict[str, GameState] = {}


def _get_game_state() -> GameState | None:
    """Return the current session's game state, if one exists."""
    game_id = session.get("game_id")
    if not isinstance(game_id, str):
        return None
    return GAME_STATES.get(game_id)


def _read_board() -> tuple[sudoku_logic.Board | None, str | None]:
    """Parse a 9x9 board without accepting booleans or out-of-range values."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    board = data.get("board")
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(
            not isinstance(row, list) or len(row) != sudoku_logic.SIZE
            for row in board
        )
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < sudoku_logic.EMPTY
            or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return None, "board must be a 9x9 grid containing values from 0 to 9"
    return board, None


def _preserves_locked_cells(
    board: sudoku_logic.Board, state: GameState
) -> bool:
    """Ensure submitted values retain all original clues and prior hints."""
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            given = state["puzzle"][row][col]
            if given != sudoku_logic.EMPTY and board[row][col] != given:
                return False

    return all(
        board[row][col] == value
        for (row, col), value in state["hints"].items()
    )


def _validate_board_for_game() -> tuple[
    GameState | None,
    sudoku_logic.Board | None,
    tuple[dict[str, str], int] | None,
]:
    """Return the active state and submitted board or a JSON error response."""
    state = _get_game_state()
    if state is None:
        return None, None, ({"error": "No game in progress"}, 400)

    board, error = _read_board()
    if error is not None:
        return None, None, ({"error": error}, 400)
    assert board is not None

    if not _preserves_locked_cells(board, state):
        return None, None, (
            {"error": "Original clues and hinted cells cannot be changed"},
            400,
        )
    return state, board, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/new")
def new_game():
    difficulty = request.args.get("difficulty")
    try:
        if difficulty is None:
            try:
                clues = int(request.args.get("clues", 35))
            except ValueError as error:
                raise ValueError("clues must be an integer") from error
            puzzle, solution = sudoku_logic.generate_puzzle(clues=clues)
        else:
            puzzle, solution = sudoku_logic.generate_puzzle(
                difficulty=difficulty
            )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError:
        app.logger.exception("Puzzle generation failed")
        return jsonify(
            {"error": "Unable to generate a puzzle. Please try again."}
        ), 503

    previous_game_id = session.get("game_id")
    if isinstance(previous_game_id, str):
        GAME_STATES.pop(previous_game_id, None)

    game_id = secrets.token_urlsafe(32)
    session["game_id"] = game_id
    GAME_STATES[game_id] = {
        "puzzle": sudoku_logic.deep_copy(puzzle),
        "solution": solution,
        "hints": {},
    }
    return jsonify({"puzzle": puzzle})


@app.route("/check", methods=["POST"])
def check_solution():
    state, board, error_response = _validate_board_for_game()
    if error_response is not None:
        response, status = error_response
        return jsonify(response), status
    assert state is not None and board is not None

    incorrect = [
        [row, col]
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if board[row][col] != sudoku_logic.EMPTY
        and board[row][col] != state["solution"][row][col]
    ]
    return jsonify(
        {
            "incorrect": incorrect,
            "complete": board == state["solution"],
            "hints_used": len(state["hints"]),
        }
    )


@app.route("/hint", methods=["POST"])
def get_hint():
    state, board, error_response = _validate_board_for_game()
    if error_response is not None:
        response, status = error_response
        return jsonify(response), status
    assert state is not None and board is not None

    empty_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if board[row][col] == sudoku_logic.EMPTY
    ]
    if not empty_cells:
        return jsonify({"error": "There are no empty cells to fill"}), 400

    row, col = random.choice(empty_cells)
    value = state["solution"][row][col]
    state["hints"][(row, col)] = value
    return jsonify(
        {
            "row": row,
            "col": col,
            "value": value,
            "hints_used": len(state["hints"]),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
