const $ = (id) => document.getElementById(id);
let activeGameId = null;
let timerInterval = null;
let displayedRemaining = 0;
let submitting = false;

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function showView(name) {
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  $("page-title").textContent = name === "play" ? "Play a game" : name === "statistics" ? "Statistics" : "Game history";
  if (name === "statistics") loadStatistics();
  if (name === "history") loadHistory();
}
document.querySelectorAll(".nav-item").forEach(b => b.addEventListener("click", () => showView(b.dataset.view)));

function selectedMode() {
  return document.querySelector('input[name="sequence"]:checked').value;
}
document.querySelectorAll('input[name="sequence"]').forEach(radio => radio.addEventListener("change", () => {
  $("fibonacci-card").classList.toggle("selected", selectedMode() === "fibonacci");
  $("powers-card").classList.toggle("selected", selectedMode() === "powers");
  $("base-field").hidden = selectedMode() !== "powers";
}));

$("setup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("setup-error").textContent = "";
  const payload = {
    sequence_type: selectedMode(),
    num_questions: Number($("num-questions").value),
    time_limit: Number($("time-limit").value),
    base: Number($("base").value)
  };
  try {
    const game = await api("/api/games", { method: "POST", body: JSON.stringify(payload) });
    activeGameId = game.game_id;
    $("setup-panel").hidden = true;
    $("results-panel").hidden = true;
    $("game-panel").hidden = false;
    $("game-mode-label").textContent = game.sequence_type.toUpperCase() + (game.base ? ` · BASE ${game.base}` : "");
    $("live-score").textContent = "0";
    $("feedback").textContent = "";
    $("feedback").className = "feedback";
    renderGame(game);
    startTimer(game.remaining_seconds);
    $("answer-input").focus();
  } catch (error) {
    $("setup-error").textContent = error.message;
  }
});

function renderGame(game) {
  if (game.finished) return showResults(game);
  const q = game.question;
  $("question-progress").textContent = `QUESTION ${q.question_number} OF ${game.num_questions}`;
  $("question-progress-bar").style.width = `${(game.question_index / game.num_questions) * 100}%`;
  $("question-prompt").textContent = q.prompt;
  $("question-hint").textContent = q.hint;
  $("sequence-display").innerHTML = "";
  if (game.sequence_type === "fibonacci") {
    q.sequence.forEach((n, i) => {
      const span = document.createElement("span");
      span.className = "sequence-number" + (i === q.sequence.length - 1 ? " latest" : "");
      span.textContent = n.toLocaleString();
      $("sequence-display").appendChild(span);
    });
    const missing = document.createElement("span");
    missing.className = "sequence-number latest";
    missing.textContent = "?";
    $("sequence-display").appendChild(missing);
  } else {
    const terms = q.sequence.length ? q.sequence : ["1st term is unknown"];
    terms.forEach((n) => {
      const span = document.createElement("span");
      span.className = "sequence-number";
      span.textContent = typeof n === "number" ? n.toLocaleString() : n;
      $("sequence-display").appendChild(span);
    });
    const missing = document.createElement("span");
    missing.className = "sequence-number latest";
    missing.textContent = "?";
    $("sequence-display").appendChild(missing);
  }
  $("live-score").textContent = game.correct;
  $("answer-input").value = "";
  $("answer-input").disabled = false;
  $("answer-form").querySelector("button").disabled = false;
  $("answer-input").focus();
}

function startTimer(seconds) {
  clearInterval(timerInterval);
  displayedRemaining = seconds;
  updateTimer();
  timerInterval = setInterval(async () => {
    displayedRemaining = Math.max(0, displayedRemaining - 0.1);
    updateTimer();
    if (displayedRemaining <= 0) {
      clearInterval(timerInterval);
      try {
        const game = await api(`/api/games/${activeGameId}`);
        if (game.finished) showResults(game);
      } catch (_) {}
    }
  }, 100);
}
function updateTimer() {
  $("timer").innerHTML = `${displayedRemaining.toFixed(1)}<span>s</span>`;
  $("timer").classList.toggle("warning", displayedRemaining <= 10);
}

$("answer-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitting || !activeGameId) return;
  const input = $("answer-input");
  if (input.value.trim() === "") return;
  submitting = true;
  input.disabled = true;
  $("answer-form").querySelector("button").disabled = true;
  try {
    const result = await api(`/api/games/${activeGameId}/answers`, {
      method: "POST", body: JSON.stringify({ answer: input.value })
    });
    if (result.last_result) {
      $("feedback").textContent = result.last_result.correct
        ? "Correct — great work!"
        : `Not quite. The correct answer was ${Number(result.last_result.expected).toLocaleString()}.`;
      $("feedback").className = "feedback " + (result.last_result.correct ? "good" : "bad");
    }
    $("live-score").textContent = result.correct;
    if (result.finished) {
      clearInterval(timerInterval);
      setTimeout(() => showResults(result), 550);
    } else {
      setTimeout(() => renderGame(result), 450);
    }
  } catch (error) {
    $("feedback").textContent = error.message;
    $("feedback").className = "feedback bad";
    input.disabled = false;
    $("answer-form").querySelector("button").disabled = false;
  } finally {
    submitting = false;
  }
});

function showResults(game) {
  clearInterval(timerInterval);
  const s = game.summary;
  if (!s) return;
  $("game-panel").hidden = true;
  $("setup-panel").hidden = true;
  $("results-panel").hidden = false;
  $("result-accuracy").textContent = `${s.accuracy}%`;
  $("accuracy-ring").style.background = `conic-gradient(#7f8cff ${s.accuracy * 3.6}deg,#293850 0deg)`;
  $("result-correct").textContent = s.correct;
  $("result-incorrect").textContent = s.incorrect;
  $("result-skipped").textContent = s.skipped;
  $("result-title").textContent = s.accuracy === 100 ? "Perfect sequence." : s.accuracy >= 70 ? "Nice work." : "Keep practicing.";
  $("result-subtitle").textContent = `${game.sequence_type === "powers" ? "Powers" : "Fibonacci"} session · ${s.elapsed_seconds.toFixed(1)} seconds`;
  $("result-icon").textContent = s.accuracy === 100 ? "★" : "✓";
  loadStatistics();
}

$("quit-game").addEventListener("click", async () => {
  if (!confirm("End this game now? Your unanswered questions will be marked as skipped.")) return;
  clearInterval(timerInterval);
  try {
    // The server ends sessions on timeout or completion. Quitting is implemented by
    // submitting a dedicated abandon request.
    const result = await api(`/api/games/${activeGameId}/abandon`, { method: "POST" });
    showResults(result);
  } catch (error) {
    alert(error.message);
  }
});
$("play-again").addEventListener("click", () => {
  $("results-panel").hidden = true;
  $("game-panel").hidden = true;
  $("setup-panel").hidden = false;
  showView("play");
});
$("view-history").addEventListener("click", () => showView("history"));

async function loadStatistics() {
  try {
    const s = await api("/api/statistics");
    $("stat-games").textContent = s.games_played;
    $("stat-average").textContent = `${s.average_accuracy}%`;
    $("stat-best").textContent = `${s.best_accuracy}%`;
    $("stat-correct").textContent = s.total_correct;
    const chart = $("accuracy-chart");
    chart.innerHTML = "";
    if (!s.recent_accuracy.length) {
      chart.innerHTML = '<div class="empty-state">Play a few games to see your accuracy trend.</div>';
    } else {
      s.recent_accuracy.forEach((value, i) => {
        const wrap = document.createElement("div");
        wrap.className = "bar-wrap";
        const bar = document.createElement("div");
        bar.className = "bar";
        bar.style.height = `${Math.max(3, value)}%`;
        bar.title = `${value}%`;
        const label = document.createElement("span");
        label.className = "bar-label";
        label.textContent = `#${i + 1}`;
        wrap.append(bar, label);
        chart.appendChild(wrap);
      });
    }
    const breakdown = $("mode-breakdown");
    breakdown.innerHTML = "";
    if (!s.by_type.length) breakdown.innerHTML = '<div class="empty-state">No games recorded yet.</div>';
    s.by_type.forEach(item => {
      const card = document.createElement("div");
      card.className = "breakdown-card";
      const name = document.createElement("div");
      const strong = document.createElement("strong");
      strong.textContent = item.sequence_type === "fibonacci" ? "Fibonacci" : "Powers";
      const small = document.createElement("small");
      small.textContent = `${item.games_played} games · ${item.total_correct} correct`;
      name.append(strong, small);
      const value = document.createElement("span");
      value.className = "breakdown-value";
      value.textContent = `${Number(item.average_accuracy).toFixed(1)}%`;
      card.append(name, value);
      breakdown.appendChild(card);
    });
  } catch (error) { console.error(error); }
}

async function loadHistory() {
  try {
    const data = await api("/api/history");
    $("history-count").textContent = `${data.games.length} GAMES`;
    const body = $("history-body");
    body.innerHTML = "";
    if (!data.games.length) {
      body.innerHTML = '<tr><td colspan="5" class="empty-state">No games played yet. Start your first session!</td></tr>';
      return;
    }
    data.games.forEach(game => {
      const tr = document.createElement("tr");
      const date = new Date(game.played_at);
      const values = [
        date.toLocaleString(),
        game.sequence_type === "fibonacci" ? "Fibonacci" : `Powers (base ${game.base})`,
        `${game.correct}/${game.num_questions}`,
        `${Number(game.accuracy).toFixed(1)}%`,
        `${Number(game.elapsed_seconds).toFixed(1)}s`
      ];
      values.forEach((value, i) => {
        const td = document.createElement("td");
        if (i === 3) {
          const pill = document.createElement("span");
          pill.className = "accuracy-pill";
          pill.textContent = value;
          td.appendChild(pill);
        } else td.textContent = value;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  } catch (error) { console.error(error); }
}
loadStatistics();
