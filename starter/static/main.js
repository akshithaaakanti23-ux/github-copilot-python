// Client-side rendering and interaction for the Flask-backed Sudoku.
const SIZE = 9;
const LEADERBOARD_STORAGE_KEY = 'sudokuTopScores';
const LEADERBOARD_LIMIT = 10;
const VALID_DIFFICULTIES = new Set(['easy', 'medium', 'hard']);
let puzzle = [];
let gameVersion = 0;
let currentDifficulty = 'medium';
let gameCompleted = false;
let scoreSaved = false;
let completedHintsUsed = 0;
let timerStartedAt = null;
let elapsedSeconds = 0;
let timerInterval = null;

function getInputs() {
  return document.querySelectorAll('#sudoku-board .sudoku-cell');
}

function setMessage(text, type = 'error') {
  const message = document.getElementById('message');
  message.textContent = text;
  message.className = type;
}

function updateTheme(isDark) {
  const toggle = document.getElementById('theme-toggle');
  document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  toggle.textContent = isDark ? 'Light mode' : 'Dark mode';
  toggle.setAttribute('aria-label', `Switch to ${isDark ? 'light' : 'dark'} mode`);
  toggle.setAttribute('aria-pressed', String(isDark));
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function updateTimer() {
  if (timerStartedAt === null) return;
  elapsedSeconds = Math.floor((Date.now() - timerStartedAt) / 1000);
  document.getElementById('timer').textContent = formatTime(elapsedSeconds);
}

function resetTimer() {
  window.clearInterval(timerInterval);
  timerStartedAt = null;
  elapsedSeconds = 0;
  document.getElementById('timer').textContent = '00:00';
}

function startTimer() {
  resetTimer();
  timerStartedAt = Date.now();
  timerInterval = window.setInterval(updateTimer, 250);
}

function stopTimer() {
  if (timerStartedAt === null) return;
  updateTimer();
  timerStartedAt = null;
  window.clearInterval(timerInterval);
}

function isValidScore(score) {
  return score !== null &&
    typeof score === 'object' &&
    typeof score.playerName === 'string' &&
    score.playerName.trim().length > 0 &&
    score.playerName.trim().length <= 30 &&
    Number.isInteger(score.timeSeconds) &&
    score.timeSeconds >= 0 &&
    VALID_DIFFICULTIES.has(score.difficulty) &&
    Number.isInteger(score.hintsUsed) &&
    score.hintsUsed >= 0;
}

function readLeaderboard() {
  const savedScores = window.localStorage.getItem(LEADERBOARD_STORAGE_KEY);
  if (savedScores === null) return [];

  let parsedScores;
  try {
    parsedScores = JSON.parse(savedScores);
  } catch {
    throw new Error('Saved leaderboard data is invalid and could not be read.');
  }
  if (!Array.isArray(parsedScores)) {
    throw new Error('Saved leaderboard data has an invalid format.');
  }

  const scores = parsedScores
    .filter(isValidScore)
    .map((score) => ({...score, playerName: score.playerName.trim()}))
    .sort((first, second) => first.timeSeconds - second.timeSeconds)
    .slice(0, LEADERBOARD_LIMIT);
  const normalizedScores = JSON.stringify(scores);
  if (savedScores !== normalizedScores) {
    window.localStorage.setItem(LEADERBOARD_STORAGE_KEY, normalizedScores);
  }
  return scores;
}

function renderLeaderboard(scores) {
  const entries = document.getElementById('leaderboard-entries');
  entries.replaceChildren();

  if (scores.length === 0) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 5;
    cell.textContent = 'No completed games yet.';
    row.appendChild(cell);
    entries.appendChild(row);
    return;
  }

  scores.forEach((score, index) => {
    const row = document.createElement('tr');
    const values = [
      String(index + 1),
      score.playerName,
      formatTime(score.timeSeconds),
      score.difficulty.charAt(0).toUpperCase() + score.difficulty.slice(1),
      String(score.hintsUsed)
    ];
    values.forEach((value) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    });
    entries.appendChild(row);
  });
}

function setLeaderboardError(message) {
  document.getElementById('leaderboard-message').textContent = message;
}

function readBoard() {
  const inputs = getInputs();
  return Array.from({length: SIZE}, (_, row) =>
    Array.from({length: SIZE}, (_, col) => {
      const value = inputs[row * SIZE + col].value;
      return value ? Number.parseInt(value, 10) : 0;
    })
  );
}

function refreshConflicts() {
  const inputs = getInputs();
  const conflicted = new Set();

  for (let index = 0; index < inputs.length; index++) {
    const value = inputs[index].value;
    if (!value) continue;

    const row = Math.floor(index / SIZE);
    const col = index % SIZE;
    for (let other = 0; other < inputs.length; other++) {
      if (other === index || inputs[other].value !== value) continue;
      const otherRow = Math.floor(other / SIZE);
      const otherCol = other % SIZE;
      const sharesBox =
        Math.floor(row / 3) === Math.floor(otherRow / 3) &&
        Math.floor(col / 3) === Math.floor(otherCol / 3);
      if (row === otherRow || col === otherCol || sharesBox) {
        conflicted.add(index);
        conflicted.add(other);
      }
    }
  }

  inputs.forEach((input, index) => {
    input.classList.toggle('conflict', conflicted.has(index));
  });
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';

  for (let row = 0; row < SIZE; row++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    rowDiv.setAttribute('role', 'row');
    for (let col = 0; col < SIZE; col++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.inputMode = 'numeric';
      input.maxLength = 1;
      input.autocomplete = 'off';
      const boxShade =
        (Math.floor(row / 3) + Math.floor(col / 3)) % 2 === 0
          ? 'box-shade-a'
          : 'box-shade-b';
      input.className = `sudoku-cell ${boxShade}`;
      input.setAttribute('role', 'gridcell');
      input.dataset.row = row;
      input.dataset.col = col;
      input.setAttribute('aria-label', `Row ${row + 1}, column ${col + 1}`);
      input.addEventListener('keydown', (event) => {
        const movement = {
          ArrowUp: [-1, 0],
          ArrowDown: [1, 0],
          ArrowLeft: [0, -1],
          ArrowRight: [0, 1]
        }[event.key];
        if (!movement) return;

        let targetRow = row + movement[0];
        let targetCol = col + movement[1];
        while (
          targetRow >= 0 &&
          targetRow < SIZE &&
          targetCol >= 0 &&
          targetCol < SIZE
        ) {
          const target = getInputs()[targetRow * SIZE + targetCol];
          if (!target.disabled) {
            event.preventDefault();
            target.focus();
            return;
          }
          targetRow += movement[0];
          targetCol += movement[1];
        }
      });
      input.addEventListener('input', (event) => {
        const cell = event.currentTarget;
        cell.value = cell.value.replace(/[^1-9]/g, '').slice(-1);
        cell.classList.remove('incorrect');
        setMessage('');
        refreshConflicts();
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(newPuzzle) {
  puzzle = newPuzzle;
  createBoardElement();
  const inputs = getInputs();

  puzzle.forEach((row, rowIndex) => {
    row.forEach((value, colIndex) => {
      const input = inputs[rowIndex * SIZE + colIndex];
      if (value !== 0) {
        input.value = value;
        input.disabled = true;
        input.classList.add('prefilled');
      }
    });
  });
}

async function readJsonResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'The request could not be completed.');
  }
  return data;
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  const version = ++gameVersion;
  gameCompleted = false;
  scoreSaved = false;
  completedHintsUsed = 0;
  resetTimer();
  document.getElementById('score-entry-form').hidden = true;
  document.getElementById('player-name').value = '';
  setMessage('');
  try {
    const response = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
    const data = await readJsonResponse(response);
    if (version !== gameVersion) return;
    renderPuzzle(data.puzzle);
    currentDifficulty = difficulty;
    document.getElementById('hint-count').textContent = 'Hints used: 0';
    setMessage('');
    startTimer();
  } catch (error) {
    if (version === gameVersion) setMessage(error.message);
  }
}

async function checkSolution() {
  const version = gameVersion;
  try {
    const response = await fetch('/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board: readBoard()})
    });
    const data = await readJsonResponse(response);
    if (version !== gameVersion) return;
    const inputs = getInputs();

    inputs.forEach((input) => input.classList.remove('incorrect'));
    data.incorrect.forEach(([row, col]) => {
      inputs[row * SIZE + col].classList.add('incorrect');
    });

    if (data.complete) {
      if (!gameCompleted) {
        gameCompleted = true;
        completedHintsUsed = data.hints_used;
        stopTimer();
        setMessage(
          `Congratulations! You solved it in ${formatTime(elapsedSeconds)} ` +
          `using ${data.hints_used} hint(s). Enter your name for the leaderboard.`,
          'success'
        );
        getInputs().forEach((input) => {
          input.disabled = true;
        });
        document.getElementById('score-entry-form').hidden = false;
        document.getElementById('player-name').focus();
      }
    } else if (data.incorrect.length > 0) {
      setMessage('Some entries are incorrect.');
    } else {
      setMessage('The board is not complete yet.');
    }
  } catch (error) {
    if (version === gameVersion) setMessage(error.message);
  }
}

async function getHint() {
  const version = gameVersion;
  try {
    const response = await fetch('/hint', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({board: readBoard()})
    });
    const data = await readJsonResponse(response);
    if (version !== gameVersion) return;
    const input = getInputs()[data.row * SIZE + data.col];
    input.value = data.value;
    input.disabled = true;
    input.classList.add('hinted');
    input.classList.remove('incorrect');
    document.getElementById('hint-count').textContent =
      `Hints used: ${data.hints_used}`;
    setMessage('');
    refreshConflicts();
  } catch (error) {
    if (version === gameVersion) setMessage(error.message);
  }
}

function saveScore(event) {
  event.preventDefault();
  if (!gameCompleted || scoreSaved) return;

  const playerName = document.getElementById('player-name').value.trim();
  if (!playerName) {
    document.getElementById('player-name').setCustomValidity(
      'Please enter your name.'
    );
    document.getElementById('player-name').reportValidity();
    return;
  }
  document.getElementById('player-name').setCustomValidity('');

  try {
    const scores = readLeaderboard();
    scores.push({
      playerName,
      timeSeconds: elapsedSeconds,
      difficulty: currentDifficulty,
      hintsUsed: completedHintsUsed
    });
    scores.sort((first, second) => first.timeSeconds - second.timeSeconds);
    const topScores = scores.slice(0, LEADERBOARD_LIMIT);
    window.localStorage.setItem(
      LEADERBOARD_STORAGE_KEY,
      JSON.stringify(topScores)
    );
    renderLeaderboard(topScores);
    setLeaderboardError('');
    document.getElementById('score-entry-form').hidden = true;
    scoreSaved = true;
    setMessage('Score saved to the leaderboard.', 'success');
  } catch (error) {
    setLeaderboardError(error.message);
  }
}

window.addEventListener('load', () => {
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const isDark = document.documentElement.dataset.theme !== 'dark';
    updateTheme(isDark);
  });
  updateTheme(false);
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('get-hint').addEventListener('click', getHint);
  document.getElementById('score-entry-form').addEventListener('submit', saveScore);
  document.getElementById('player-name').addEventListener('input', (event) => {
    event.currentTarget.setCustomValidity('');
  });
  try {
    renderLeaderboard(readLeaderboard());
  } catch (error) {
    setLeaderboardError(error.message);
    renderLeaderboard([]);
  }
  newGame();
});
