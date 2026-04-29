const starterSelect = document.querySelector("#starter");
const profileSelect = document.querySelector("#profile");
const modeSelect = document.querySelector("#mode");
const outputInput = document.querySelector("#output");
const selectionSummary = document.querySelector("#selection-summary");
const resultView = document.querySelector("#result");
const generateButton = document.querySelector("#generate");
const refreshButton = document.querySelector("#refresh");

let starters = [];

function relativeOutput(starterId, mode, profileId) {
  return [".tmp", "starter-ui", mode, starterId, profileId].join("/");
}

function currentStarter() {
  return starters.find((starter) => starter.starter_id === starterSelect.value);
}

function currentProfile() {
  const starter = currentStarter();
  return starter?.profiles?.[profileSelect.value] ?? null;
}

function updateModeOptions(starter) {
  modeSelect.innerHTML = "";
  for (const mode of starter.generation_modes) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    if (mode === starter.default_generation_mode) {
      option.selected = true;
    }
    modeSelect.appendChild(option);
  }
}

function updateProfileOptions(starter) {
  profileSelect.innerHTML = "";
  for (const [profileId] of Object.entries(starter.profiles)) {
    const option = document.createElement("option");
    option.value = profileId;
    option.textContent = profileId;
    if (profileId === starter.default_profile) {
      option.selected = true;
    }
    profileSelect.appendChild(option);
  }
}

function renderSelection() {
  const starter = currentStarter();
  const profile = currentProfile();
  if (!starter || !profile) {
    selectionSummary.textContent = "No starter selected.";
    return;
  }

  const features = profile.features.length ? profile.features.join(", ") : "none";
  const scenarios = profile.scenarios.length ? profile.scenarios.join(", ") : "none";
  const proofScenarios = profile.proof_scenarios.length ? profile.proof_scenarios.join(", ") : "none";
  const publishedImage = starter.published_image ?? "n/a";

  selectionSummary.innerHTML = `
    <p><strong>${starter.title}</strong></p>
    <p>${starter.description}</p>
    <p><strong>Language:</strong> ${starter.language}</p>
    <p><strong>Profile:</strong> ${profile.profile_id}</p>
    <p><strong>Features:</strong> ${features}</p>
    <p><strong>Scenarios:</strong> ${scenarios}</p>
    <p><strong>Proof scenarios:</strong> ${proofScenarios}</p>
    <p><strong>Published image:</strong> ${publishedImage}</p>
  `;
}

function syncOutput() {
  const starter = currentStarter();
  const profile = currentProfile();
  if (!starter || !profile) {
    return;
  }
  outputInput.value = relativeOutput(starter.starter_id, modeSelect.value, profile.profile_id);
}

function setResult(payload) {
  resultView.textContent = JSON.stringify(payload, null, 2);
}

async function loadCatalog() {
  setResult({ status: "loading catalog" });
  const response = await fetch("/api/catalog");
  const payload = await response.json();
  starters = payload.starters ?? [];
  starterSelect.innerHTML = "";
  for (const starter of starters) {
    const option = document.createElement("option");
    option.value = starter.starter_id;
    option.textContent = starter.title;
    starterSelect.appendChild(option);
  }
  if (starters.length > 0) {
    starterSelect.value = starters[0].starter_id;
    onStarterChange();
  }
  setResult(payload);
}

function onStarterChange() {
  const starter = currentStarter();
  if (!starter) {
    return;
  }
  updateProfileOptions(starter);
  updateModeOptions(starter);
  syncOutput();
  renderSelection();
}

function onProfileOrModeChange() {
  syncOutput();
  renderSelection();
}

async function generateStarter() {
  const starter = currentStarter();
  const profile = currentProfile();
  if (!starter || !profile) {
    return;
  }
  generateButton.disabled = true;
  setResult({ status: "generating" });
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        starter: starter.starter_id,
        profile: profile.profile_id,
        mode: modeSelect.value,
        output: outputInput.value,
        force: true,
      }),
    });
    const payload = await response.json();
    setResult(payload);
  } finally {
    generateButton.disabled = false;
  }
}

starterSelect.addEventListener("change", onStarterChange);
profileSelect.addEventListener("change", onProfileOrModeChange);
modeSelect.addEventListener("change", onProfileOrModeChange);
generateButton.addEventListener("click", generateStarter);
refreshButton.addEventListener("click", loadCatalog);

loadCatalog().catch((error) => {
  setResult({ error: String(error) });
});
