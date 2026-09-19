"""
Phase E4 tool: renders questionnaire.json (written by `python -m src.elicitation`)
into the elicitation questionnaire's HTML/JS, ready to publish as an Artifact
(see ATOMIC_KEYPRESS_REWIRE_PLAN.md's open decision §F -- resolved to a web page
with checkboxes and a save button backed by the Artifact `db` capability).
"""
import json
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(_REPO_ROOT, "questionnaire.json"), encoding="utf-8") as f:
    items = json.load(f)

LABELS = {
    "pers_1": "1re pers.", "pers_2": "2e pers.", "pers_3": "3e pers.",
    "nbr_s": "nombre: sing.", "nbr_p": "nombre: plur.",
    "s": "singulier", "p": "pluriel", "m": "masculin", "f": "féminin",
    "indicatif": "indicatif", "subjonctif": "subjonctif", "conditionnel": "conditionnel",
    "impératif": "impératif", "infinitif": "infinitif", "présent": "présent",
    "imparfait": "imparfait", "future": "futur", "passé": "passé",
    "participe": "participe", "VER": "verbe (≠ nom)",
}

HTML_TEMPLATE = r"""<title>Élicitation sténo</title>
<style>
:root {
  --bg: #f4f3ef;
  --paper: #ffffff;
  --ink: #23241f;
  --ink-soft: #5a5b52;
  --line: #dcdad0;
  --accent: #2c4a7c;
  --accent-soft: #e4ecf7;
  --accent-ink: #17304f;
  --warn: #9a5b1e;
  --warn-soft: #f7ead9;
  --key-bg: #ecebe4;
  --key-bg-on: #2c4a7c;
  --key-ink-on: #f4f3ef;
  --good: #3d6b3d;
  --good-soft: #e3ede2;
  --shadow: 0 1px 2px rgba(30,30,20,0.06), 0 1px 1px rgba(30,30,20,0.04);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #1b1c19;
    --paper: #232420;
    --ink: #ecebe4;
    --ink-soft: #a8a89c;
    --line: #37372f;
    --accent: #7fa2d9;
    --accent-soft: #26344a;
    --accent-ink: #dbe6f5;
    --warn: #d9a066;
    --warn-soft: #3a2f1e;
    --key-bg: #2d2e28;
    --key-bg-on: #7fa2d9;
    --key-ink-on: #1b1c19;
    --good: #8fbf8a;
    --good-soft: #26332a;
    --shadow: 0 1px 2px rgba(0,0,0,0.3);
  }
}
:root[data-theme="dark"] {
  --bg: #1b1c19;
  --paper: #232420;
  --ink: #ecebe4;
  --ink-soft: #a8a89c;
  --line: #37372f;
  --accent: #7fa2d9;
  --accent-soft: #26344a;
  --accent-ink: #dbe6f5;
  --warn: #d9a066;
  --warn-soft: #3a2f1e;
  --key-bg: #2d2e28;
  --key-bg-on: #7fa2d9;
  --key-ink-on: #1b1c19;
  --good: #8fbf8a;
  --good-soft: #26332a;
  --shadow: 0 1px 2px rgba(0,0,0,0.3);
}

* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: "Work Sans", system-ui, sans-serif;
  margin: 0;
  padding-inline: 16px;
  padding-block: 12px 48px;
}
h1, h2 { font-family: "Fraunces", Georgia, serif; }

.wrap { max-width: 900px; margin: 0 auto; }

header.top {
  position: sticky;
  top: env(safe-area-inset-top, 0px);
  z-index: 10;
  background: var(--bg);
  padding-block: 10px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 18px;
}
.top-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.top-row h1 {
  font-size: 1.25rem;
  margin: 0;
  flex: 1 1 auto;
  min-width: 160px;
  text-wrap: balance;
}
.progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--ink-soft);
}
.progress-bar {
  width: 100px;
  height: 6px;
  border-radius: 3px;
  background: var(--line);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--good);
  width: 0%;
  transition: width 0.2s ease;
}
button.save {
  font: inherit;
  font-weight: 600;
  background: var(--accent);
  color: var(--paper);
  border: none;
  border-radius: 8px;
  padding: 9px 18px;
  cursor: pointer;
}
button.save:active { transform: translateY(1px); }
.status {
  font-size: 0.78rem;
  color: var(--ink-soft);
  min-width: 140px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  align-items: center;
}
.filters input[type="search"] {
  font: inherit;
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--paper);
  color: var(--ink);
  flex: 1 1 160px;
  min-width: 0;
}
.chip {
  font: inherit;
  font-size: 0.8rem;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink-soft);
  cursor: pointer;
}
.chip.active {
  background: var(--accent-soft);
  color: var(--accent-ink);
  border-color: var(--accent);
  font-weight: 600;
}

.card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
}
.card.reviewed { opacity: 0.6; }
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.card-eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-soft);
}
.card-eyebrow .lemma { color: var(--accent); font-weight: 600; }
.badge-warn {
  font-size: 0.68rem;
  background: var(--warn-soft);
  color: var(--warn);
  padding: 2px 7px;
  border-radius: 999px;
  font-weight: 600;
  white-space: nowrap;
}
label.reviewed-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
  color: var(--ink-soft);
  cursor: pointer;
  user-select: none;
}
.sides {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 560px) {
  .sides { grid-template-columns: 1fr; }
}
.side h2 {
  font-size: 1.35rem;
  margin: 0 0 8px;
}
.keys {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.key {
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.78rem;
  background: var(--key-bg);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 6px 9px;
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.key input { accent-color: var(--accent); margin: 0; }
.key.on {
  background: var(--key-bg-on);
  color: var(--key-ink-on);
  border-color: var(--key-bg-on);
}
.empty {
  text-align: center;
  color: var(--ink-soft);
  padding: 40px 0;
}
footer.note {
  max-width: 900px;
  margin: 24px auto 0;
  font-size: 0.78rem;
  color: var(--ink-soft);
  line-height: 1.5;
}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Work+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">

<div class="wrap">
  <header class="top">
    <div class="top-row">
      <h1>Élicitation sténo — marqueurs</h1>
      <div class="progress-wrap">
        <span id="progressLabel">0 / 0 décidées</span>
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
      </div>
      <button class="save" id="saveBtn">Enregistrer</button>
    </div>
    <div class="status" id="statusLine">Non enregistré.</div>
    <div class="filters">
      <input type="search" id="search" placeholder="Filtrer par lemme ou mot…">
      <button class="chip active" data-filter="all">Toutes (<span id="countAll">0</span>)</button>
      <button class="chip" data-filter="todo">À décider (<span id="countTodo">0</span>)</button>
      <button class="chip" data-filter="risky">Homographe ⚠ (<span id="countRisky">0</span>)</button>
    </div>
  </header>

  <main id="list"></main>
  <div class="empty" id="emptyState" hidden>Aucune question ne correspond au filtre.</div>

  <footer class="note">
    Pour chaque paire, cochez les marqueurs minimums que vous presseriez réellement pour écrire
    ce mot — laisser tout décoché signifie "je tape la forme nue, sans presse" (∅). Cochez
    "Décidé" une fois votre choix arrêté, même si ce choix est de ne rien presser. Vos réponses
    sont sauvegardées dans votre navigateur automatiquement ; le bouton "Enregistrer" les
    partage pour que l'analyse (Phase G) puisse les lire.
  </footer>
</div>

<script>
const QUESTIONS = __QUESTIONS_JSON__;
const LABELS = __LABELS_JSON__;
const STORAGE_KEY = "stenalgo-elicitation-v1";

let state = {};
let userHasEdited = false;
try {
  state = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
} catch (e) { state = {}; }

function getEntry(id) {
  if (!state[id]) state[id] = { a: [], b: [], reviewed: false };
  return state[id];
}

function persistLocal() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
}

function label(atom) { return LABELS[atom] || atom; }

function renderKey(qid, side, atom) {
  const entry = getEntry(qid);
  const checked = entry[side].includes(atom);
  const id = qid + "_" + side + "_" + atom;
  const div = document.createElement("label");
  div.className = "key" + (checked ? " on" : "");
  div.setAttribute("for", id);
  div.innerHTML =
    '<input type="checkbox" id="' + id + '"' + (checked ? " checked" : "") + '>' +
    '<span>' + atom + " · " + label(atom) + "</span>";
  const input = div.querySelector("input");
  input.addEventListener("change", () => {
    const entry = getEntry(qid);
    const list = entry[side];
    const idx = list.indexOf(atom);
    if (input.checked && idx === -1) list.push(atom);
    if (!input.checked && idx !== -1) list.splice(idx, 1);
    div.classList.toggle("on", input.checked);
    userHasEdited = true;
    persistLocal();
  });
  return div;
}

function renderCard(q) {
  const entry = getEntry(q.id);
  const card = document.createElement("article");
  card.className = "card" + (entry.reviewed ? " reviewed" : "");
  card.dataset.id = q.id;

  const head = document.createElement("div");
  head.className = "card-head";
  head.innerHTML =
    '<div class="card-eyebrow">' + q.numLabel + ' &middot; lemme <span class="lemma">' + q.lemma + '</span>' +
    (q.clean ? "" : ' &nbsp;<span class="badge-warn">⚠ homographe proche</span>') + '</div>';

  const reviewLabel = document.createElement("label");
  reviewLabel.className = "reviewed-toggle";
  const reviewInput = document.createElement("input");
  reviewInput.type = "checkbox";
  reviewInput.checked = entry.reviewed;
  reviewInput.addEventListener("change", () => {
    getEntry(q.id).reviewed = reviewInput.checked;
    card.classList.toggle("reviewed", reviewInput.checked);
    userHasEdited = true;
    persistLocal();
    updateProgress();
    applyFilter();
  });
  reviewLabel.appendChild(reviewInput);
  reviewLabel.appendChild(document.createTextNode("Décidé"));
  head.appendChild(reviewLabel);
  card.appendChild(head);

  const sides = document.createElement("div");
  sides.className = "sides";
  [["a", q.orthoA, q.atomsA], ["b", q.orthoB, q.atomsB]].forEach(([side, ortho, atoms]) => {
    const box = document.createElement("div");
    box.className = "side";
    const h = document.createElement("h2");
    h.textContent = ortho;
    box.appendChild(h);
    const keys = document.createElement("div");
    keys.className = "keys";
    if (atoms.length === 0) {
      const none = document.createElement("span");
      none.style.fontSize = "0.8rem";
      none.style.color = "var(--ink-soft)";
      none.textContent = "(aucun marqueur — forme nue)";
      keys.appendChild(none);
    } else {
      atoms.forEach(atom => keys.appendChild(renderKey(q.id, side, atom)));
    }
    box.appendChild(keys);
    sides.appendChild(box);
  });
  card.appendChild(sides);
  return card;
}

let currentFilter = "all";
let currentSearch = "";

function matchesFilter(q) {
  const entry = getEntry(q.id);
  if (currentFilter === "todo" && entry.reviewed) return false;
  if (currentFilter === "risky" && q.clean) return false;
  if (currentSearch) {
    const s = currentSearch.toLowerCase();
    if (!q.lemma.toLowerCase().includes(s) && !q.orthoA.toLowerCase().includes(s) &&
        !q.orthoB.toLowerCase().includes(s)) return false;
  }
  return true;
}

const listEl = document.getElementById("list");
const emptyEl = document.getElementById("emptyState");

function applyFilter() {
  listEl.innerHTML = "";
  const matched = QUESTIONS.filter(matchesFilter);
  emptyEl.hidden = matched.length > 0;
  const frag = document.createDocumentFragment();
  matched.forEach(q => frag.appendChild(renderCard(q)));
  listEl.appendChild(frag);
}

function updateProgress() {
  const total = QUESTIONS.length;
  const done = QUESTIONS.filter(q => getEntry(q.id).reviewed).length;
  document.getElementById("progressLabel").textContent = done + " / " + total + " décidées";
  document.getElementById("progressFill").style.width = (total ? (100 * done / total) : 0) + "%";
  document.getElementById("countAll").textContent = total;
  document.getElementById("countTodo").textContent = total - done;
  document.getElementById("countRisky").textContent = QUESTIONS.filter(q => !q.clean).length;
}

document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    currentFilter = chip.dataset.filter;
    applyFilter();
  });
});
document.getElementById("search").addEventListener("input", (e) => {
  currentSearch = e.target.value;
  applyFilter();
});

applyFilter();
updateProgress();

// ---- db capability: load shared answers, and wire the Save button ----
const statusLine = document.getElementById("statusLine");
let dbRef = null;

(async () => {
  try {
    const db = await claude.use("db");
    if (!db) { statusLine.textContent = "Stockage partagé indisponible — sauvegarde locale seulement."; return; }
    dbRef = db.doc("progress/answers");
    const snap = await dbRef.get();
    if (snap.exists) {
      const data = snap.data();
      if (data && data.answers) {
        if (userHasEdited) {
          statusLine.textContent = "Réponses partagées ignorées (vous aviez déjà commencé à répondre) — Enregistrer écrasera la version partagée.";
        } else {
          state = data.answers;
          persistLocal();
          applyFilter();
          updateProgress();
        }
      }
      if (data && data.savedAt) {
        statusLine.textContent = "Dernière sauvegarde partagée : " + new Date(data.savedAt).toLocaleString();
      }
    }
  } catch (e) {
    statusLine.textContent = "Stockage partagé indisponible — sauvegarde locale seulement.";
  }
})();

document.getElementById("saveBtn").addEventListener("click", async () => {
  persistLocal();
  statusLine.textContent = "Enregistrement…";
  try {
    if (!dbRef) {
      const db = await claude.use("db");
      if (!db) { statusLine.textContent = "Sauvegarde locale seulement (stockage partagé indisponible)."; return; }
      dbRef = db.doc("progress/answers");
    }
    const done = QUESTIONS.filter(q => getEntry(q.id).reviewed).length;
    await dbRef.set({ answers: state, savedAt: new Date().toISOString(), reviewedCount: done, total: QUESTIONS.length });
    statusLine.textContent = "Enregistré à " + new Date().toLocaleTimeString();
  } catch (e) {
    statusLine.textContent = "Échec de l'enregistrement partagé (conservé localement).";
  }
});
</script>
"""


def main() -> None:
    for i, item in enumerate(items):
        item["numLabel"] = f"Q{i + 1}/{len(items)}"
    html = HTML_TEMPLATE.replace("__QUESTIONS_JSON__", json.dumps(items, ensure_ascii=False))
    html = html.replace("__LABELS_JSON__", json.dumps(LABELS, ensure_ascii=False))
    out_path = os.path.join(_REPO_ROOT, "elicitation_questionnaire.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", out_path, len(html), "bytes")


if __name__ == "__main__":
    main()
