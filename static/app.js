const form = document.getElementById("analyzeForm");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("errorBox");
const submitBtn = document.getElementById("submitBtn");

const emptyState = document.getElementById("emptyState");
const result = document.getElementById("result");

const scoreValue = document.getElementById("scoreValue");
const scorePill = document.getElementById("scorePill");
const scoreHint = document.getElementById("scoreHint");

const jdKeywords = document.getElementById("jdKeywords");
const missingKeywords = document.getElementById("missingKeywords");
const suggestions = document.getElementById("suggestions");

const progressBar = document.getElementById("progressBar");
const progressLabel = document.getElementById("progressLabel");

function setProgress(p) {
  const clamped = Math.max(0, Math.min(100, p));
  progressBar.style.width = `${clamped}%`;
  progressLabel.textContent = `${clamped}%`;
}

function chip(text) {
  const el = document.createElement("span");
  el.className = "chip";
  el.textContent = text;
  return el;
}

function setChips(container, items) {
  container.innerHTML = "";
  if (!items || items.length === 0) {
    container.appendChild(chip("None"));
    return;
  }
  items.forEach(it => container.appendChild(chip(it)));
}

function scoreLabel(score) {
  if (score >= 75) return { label: "High match", hint: "Strong alignment with the job description." };
  if (score >= 50) return { label: "Medium match", hint: "Good alignment—close key gaps for a better fit." };
  return { label: "Low match", hint: "Add relevant experience/skills to better match the role." };
}

function setSuggestions(suggs) {
  suggestions.innerHTML = "";
  (suggs || []).forEach(s => {
    const card = document.createElement("div");
    card.className = "sugg-card";
    card.innerHTML = `
      <h6>${s.title}</h6>
      <ul>
        ${(s.details || []).map(d => `<li>${d}</li>`).join("")}
      </ul>
    `;
    suggestions.appendChild(card);
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  errorBox.classList.add("d-none");
  emptyState.classList.remove("d-none");
  result.classList.add("d-none");

  loading.classList.remove("d-none");
  submitBtn.disabled = true;

  try {
    setProgress(10);

    const fd = new FormData(form);

    setProgress(25);

    const res = await fetch("/api/analyze/", {
      method: "POST",
      body: fd
    });

    setProgress(60);

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }

    setProgress(85);

    const score = Number(data.similarity_score ?? 0);
    scoreValue.textContent = score.toFixed(2);

    const meta = scoreLabel(score);
    scorePill.textContent = meta.label;
    scoreHint.textContent = meta.hint;

    const improvements = data.improvements || {};
    setChips(jdKeywords, improvements.top_keywords_from_jd);
    setChips(missingKeywords, improvements.missing_keywords);
    setSuggestions(improvements.suggestions);

    emptyState.classList.add("d-none");
    result.classList.remove("d-none");

    setProgress(100);

    // nice UX reset after short delay
    setTimeout(() => setProgress(0), 600);

  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("d-none");
  } finally {
    loading.classList.add("d-none");
    submitBtn.disabled = false;
  }
});