const promptEl = document.getElementById("prompt");
const planEl = document.getElementById("plan");
const resultsEl = document.getElementById("results");
const planBtn = document.getElementById("plan-btn");
const executeBtn = document.getElementById("execute-btn");
const destructiveEl = document.getElementById("destructive");

let currentPlan = null;

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

planBtn.addEventListener("click", async () => {
  resultsEl.textContent = "Nothing executed.";
  try {
    currentPlan = await post("/api/plan", { prompt: promptEl.value });
    planEl.textContent = JSON.stringify(currentPlan, null, 2);
    executeBtn.disabled = false;
  } catch (error) {
    currentPlan = null;
    executeBtn.disabled = true;
    planEl.textContent = error.message;
  }
});

executeBtn.addEventListener("click", async () => {
  if (!currentPlan) {
    return;
  }
  try {
    const data = await post("/api/execute", {
      plan: currentPlan,
      confirm: true,
      destructive_confirm: destructiveEl.checked,
    });
    resultsEl.textContent = JSON.stringify(data.results, null, 2);
  } catch (error) {
    resultsEl.textContent = error.message;
  }
});
