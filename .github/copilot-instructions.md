# GitHub Copilot Instructions — Sudoku Flask Project

## Project Context
Refactor a legacy Python Flask Sudoku game into a modular, maintainable, responsive application. Preserve existing functionality while implementing the Udacity rubric.

## Python and Flask Standards
- Follow PEP 8 and use descriptive names.
- Write small, reusable functions with clear responsibilities.
- Separate Sudoku generation, solving, validation, Flask routes, and frontend behavior where practical.
- Add type hints and concise docstrings for nontrivial functions.
- Handle invalid inputs and errors consistently.
- Avoid unnecessary dependencies and large rewrites.
- Never expose puzzle solutions in client-side code or API responses.

## Sudoku Requirements
- Generate valid 9x9 Sudoku puzzles with exactly one solution.
- Support Easy, Medium, and Hard difficulties with different clue counts.
- Lock original clues and hint-filled cells.
- Provide immediate visual feedback for conflicting moves.
- Implement a Check button, Hint button, timer, and completion message.
- Store the 10 fastest completed games in localStorage with player name, time, difficulty, and hint count.

## UI Requirements
- Use responsive HTML, CSS, and JavaScript.
- Alternate background colors between 3x3 Sudoku regions.
- Support readable light and dark themes.
- Maintain accessible labels, keyboard navigation, and clear focus indicators.

## Testing and Workflow
- Before refactoring, establish a passing baseline test suite using pytest.
- Do not change application behavior when setting up baseline tests.
- Run tests after every significant modification.
- Add tests for unique solutions, difficulties, validation, and relevant Flask routes.
- Explain proposed changes before making major edits.
- Make incremental changes and allow review of suggestions.
- If a suggestion is unsafe, incorrect, or unnecessary, explain why and offer an alternative.
- Keep README instructions for installation, running, and testing up to date.
- Do not fabricate test results or Copilot interaction evidence.