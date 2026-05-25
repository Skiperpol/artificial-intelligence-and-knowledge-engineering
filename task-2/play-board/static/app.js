const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const helpEl = document.getElementById("help");
const sideSelect = document.getElementById("human-side");
const btnNew = document.getElementById("btn-new");

let state = null;
let selected = null;
let dragFrom = null;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function movesFrom(cell) {
  if (!state?.legal_moves) return [];
  return state.legal_moves.filter(
    (m) => m.from_row === cell.row && m.from_col === cell.col
  );
}

function targetsForSelection() {
  if (!selected) return new Set();
  const moves = movesFrom(selected);
  const keys = new Set();
  for (const m of moves) keys.add(`${m.to_row},${m.to_col}`);
  return keys;
}

function setBusy(busy) {
  boardEl.classList.toggle("busy", busy);
}

function render() {
  boardEl.innerHTML = "";
  if (!state?.active) {
    statusEl.textContent = "Brak gry — kliknij Nowa gra.";
    return;
  }

  const { grid, rows, cols, human_symbol, turn, winner, message, last_from } =
    state;
  const targets = targetsForSelection();

  if (winner === "human") statusEl.textContent = "Wygrałeś!";
  else if (winner === "bot") statusEl.textContent = "Wygrał bot.";
  else if (turn === "bot") statusEl.textContent = "Bot myśli…";
  else statusEl.textContent = message || "Twój ruch.";

  boardEl.style.gridTemplateColumns = `repeat(${cols}, var(--cell))`;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("div");
      cell.className = "cell " + ((r + c) % 2 === 0 ? "light" : "dark");
      cell.dataset.row = String(r);
      cell.dataset.col = String(c);

      const key = `${r},${c}`;
      if (targets.has(key)) cell.classList.add("target");
      if (
        last_from &&
        last_from.from_row === r &&
        last_from.from_col === c
      ) {
        cell.classList.add("last-from");
      }

      const sym = grid[r][c];
      if (sym === "B" || sym === "W") {
        const piece = document.createElement("div");
        piece.className = `piece ${sym}`;
        piece.draggable =
          turn === "human" &&
          sym === human_symbol &&
          !winner;
        if (
          selected &&
          selected.row === r &&
          selected.col === c
        ) {
          piece.classList.add("selected");
        }
        piece.addEventListener("dragstart", onDragStart);
        piece.addEventListener("click", (e) => {
          e.stopPropagation();
          onPieceClick(r, c, sym);
        });
        cell.appendChild(piece);
      }

      cell.addEventListener("click", () => onCellClick(r, c));
      cell.addEventListener("dragover", (e) => {
        if (targets.has(key)) {
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";
        }
      });
      cell.addEventListener("drop", (e) => {
        e.preventDefault();
        onDrop(r, c);
      });

      boardEl.appendChild(cell);
    }
  }
}

function onPieceClick(row, col, sym) {
  if (!state || state.turn !== "human" || state.winner) return;
  if (sym !== state.human_symbol) return;

  if (
    selected &&
    selected.row === row &&
    selected.col === col
  ) {
    selected = null;
    render();
    return;
  }

  selected = { row, col };
  render();
}

function onCellClick(row, col) {
  if (!selected || !state || state.turn !== "human" || state.winner) return;
  const move = movesFrom(selected).find(
    (m) => m.to_row === row && m.to_col === col
  );
  if (move) submitMove(move);
}

function highlightTargets() {
  const targets = targetsForSelection();
  boardEl.querySelectorAll(".cell").forEach((cell) => {
    const r = Number(cell.dataset.row);
    const c = Number(cell.dataset.col);
    cell.classList.toggle("target", targets.has(`${r},${c}`));
  });
}

function onDragStart(e) {
  const cell = e.target.parentElement;
  dragFrom = {
    row: Number(cell.dataset.row),
    col: Number(cell.dataset.col),
  };
  selected = dragFrom;
  highlightTargets();
  e.dataTransfer.setData("text/plain", "piece");
  e.dataTransfer.effectAllowed = "move";
}

function onDrop(toRow, toCol) {
  const from = dragFrom || selected;
  if (!from) return;
  const move = movesFrom(from).find(
    (m) => m.to_row === toRow && m.to_col === toCol
  );
  if (move) submitMove(move);
  dragFrom = null;
}

async function submitMove(move) {
  selected = null;
  setBusy(true);
  try {
    state = await api("/api/move", {
      method: "POST",
      body: JSON.stringify({
        from_row: move.from_row,
        from_col: move.from_col,
        to_row: move.to_row,
        to_col: move.to_col,
      }),
    });
    render();
  } catch (err) {
    statusEl.textContent = err.message;
    helpEl.textContent = "Spróbuj innego ruchu.";
  } finally {
    setBusy(false);
  }
}

async function newGame() {
  selected = null;
  setBusy(true);
  try {
    state = await api("/api/new", {
      method: "POST",
      body: JSON.stringify({ human_side: sideSelect.value }),
    });
    render();
  } catch (err) {
    statusEl.textContent = "Błąd: " + err.message;
  } finally {
    setBusy(false);
  }
}

btnNew.addEventListener("click", newGame);
sideSelect.addEventListener("change", () => {
  helpEl.textContent =
    "Zmiana koloru — uruchom „Nowa gra”, żeby zacząć od nowa.";
});

newGame();
