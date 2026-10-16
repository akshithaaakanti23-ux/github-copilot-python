# Refactor a Sudoku Game written in Python Flask

Use this simple Sudoku game as a starting point to practice your skills with GitHub Copilot. The goal is to refactor the code to use modern technologies, while also adding new features and improving the overall user experience.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Dependencies

```
- Modern web browser (Chrome, Firefox, Edge, etc.)
- Python 3
```

### Installation

1. Fork this repository to your GitHub account. (You can use the "Fork" button on the top right corner of the repository page.)

2. Clone your forked repository to your local machine.

3. Open a terminal window and navigate to the "github-copilot-python/starter" directory.

4. Create a Python virtual environment and activate it (optional but highly recommended).

```bash
python3 -m venv .venv
source .venv/bin/activate
```

5. Install required Python packages.

```bash
pip install -r requirements.txt
```

6. Run the Flask app.

```bash
python app.py
```

7. Open http://127.0.0.1:5000 in your browser.

### Running pytest

From the `starter` directory, install the development requirements and run
pytest:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The `/new` route accepts `difficulty=easy`, `difficulty=medium`, or
`difficulty=hard`. Generated puzzles retain a unique solution and use these
inclusive clue-count bands: Easy 40-45, Medium 33-39, and Hard 28-32. For
backward compatibility, `/new` without a difficulty still defaults to 35
clues, and `/new?clues=35` continues to request an exact clue count.

## Gameplay

Choose Easy, Medium, or Hard before starting a new game. Repeated values in a
row, column, or 3x3 box are highlighted as soon as they are entered. **Check
Solution** marks incorrect filled cells without returning the solution to the
browser; a congratulatory message appears only after the board is complete and
correct. The MM:SS timer starts with each new puzzle and stops only after the
server confirms a correct solution. After solving, enter a name to save the
completion time, difficulty, and hint count in the browser's localStorage.
The leaderboard keeps and displays the 10 fastest valid completed games;
incomplete and incorrectly solved puzzles are not recorded. **Hint** fills and
locks one empty cell at a time. The page displays the number of hints used in
the current game.

## Project Instructions

Use GitHub Copilot to refactor the code for this game to add more advanced features. The goal is to create a more modern and maintainable codebase and add additional functionality to the final product. You can use any combination of code completion and chat features, like Ask, Edit, or Agent modes.

- Errors should be handled gracefully with appropriate messages to the user.
- Implement a Sudoku board generator that creates a valid Sudoku puzzle with a unique solution.
- Add a timer to track how long it takes to solve the puzzle.
- Implement a solution checker that verifies if the user's solution is correct using event delegation.
- Add a difficulty selector to allow users to choose between easy, medium, and hard puzzles.
- Add a hint feature that provides clues for the user that are noted with unique colors.
- Add a check puzzle button that checks the current state of the board against the solution.
- User should get immediate feedback on their input, such as highlighting invalid entries.
- Top 10 scores should be saved in local storage and displayed on the page with the user's name, time taken, hints used, and difficulty level.
- The game should be responsive and work well on both desktop and mobile devices.
- UI colors should be visually appealing and accessible.
- Completed and correct puzzles should display a congratulatory message with the time taken and hints used and ask for the user's name for Top 10 times.
