const LOCAL_MODEL = "meta-llama/llama-3.2-3b-instruct:free";
const CLOUD_MODEL = "google/gemma-4-26b-a4b-it:free";
const LOCAL_FALLBACK_MODELS = [
  LOCAL_MODEL,
  "liquid/lfm-2.5-1.2b-instruct:free",
  "openai/gpt-oss-20b:free",
  "openrouter/free",
];
const CLOUD_FALLBACK_MODELS = [
  CLOUD_MODEL,
  "openai/gpt-oss-120b:free",
  "qwen/qwen3-next-80b-a3b-instruct:free",
  "openrouter/free",
];
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

const API_INTENT_KEYWORDS = {
  weather: ["weather", "temperature", "forecast", "rain", "snow", "humidity", "wind"],
  crypto: ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "dogecoin", "doge", "token", "coin", "price"],
  news: ["news", "headline", "breaking", "latest news", "today's news", "current events"],
};

const REALTIME_KEYWORDS = ["current", "latest", "today", "now", "right now", "this week", "this month", "recent", "trading", "market cap", "stock", ...Object.values(API_INTENT_KEYWORDS).flat()];
const COMPLEX_MARKERS = ["write a detailed", "write an essay", "write a report", "write a paper", "write an article", "draft a", "comprehensive analysis", "detailed analysis", "in-depth analysis", "analyze in detail", "deep dive into", "compare and contrast", "compare all", "differences between", "similarities and differences", "step-by-step tutorial", "step by step", "walk me through", "guide me through", "explain step by step", "explain in depth", "explain thoroughly", "explain comprehensively", "provide a detailed explanation", "go into detail", "quantum", "derive the", "prove that", "proof of", "theorem", "algorithm analysis", "big o notation", "differential equation", "integral of", "list all", "enumerate all", "every single", "all possible", "write a story", "write a poem", "create a narrative", "research on", "literature review", "survey of"];
const SPECIALIZED_DOMAINS = ["quantum chromodynamics", "string theory", "general relativity", "thermodynamics", "organic chemistry", "topology", "number theory", "abstract algebra", "differential geometry", "complex analysis", "blockchain consensus", "zero-knowledge proof", "compiler optimization", "kernel development"];
const ENERGY = { localJPerToken: 0.85, cloudJPerToken: 3.10, apiWh: 0.001, joulesPerWh: 3600 };
const statusLabels = { local_starting: "Routing to local-class model", api_fetching: "Checking current-data intent", cloud_processing: "Routing to cloud-class model", complete: "Response complete" };
const reasonLabels = { empty_prompt: "Empty prompt", needs_realtime_data: "Needs current data", specialized_domain: "Specialized domain", too_complex_for_small_model: "Too complex for small model", prompt_too_long: "Prompt too long", default_energy_saving: "Default energy-saving route", waiting: "Waiting" };

const els = {
  appShell: document.querySelector(".app-shell"),
  runtimePill: document.querySelector("#runtime-pill"),
  liveToggle: document.querySelector("#live-toggle"),
  keyInput: document.querySelector("#api-key-input"),
  saveKeyButton: document.querySelector("#save-key-button"),
  clearKeyButton: document.querySelector("#clear-key-button"),
  clearChatsButton: document.querySelector("#clear-chats-button"),
  homeButton: document.querySelector("#home-button"),
  newChatButton: document.querySelector("#new-chat-button"),
  closeChatButton: document.querySelector("#close-chat-button"),
  homeScreen: document.querySelector("#home-screen"),
  chatScreen: document.querySelector("#chat-screen"),
  homeForm: document.querySelector("#home-prompt-form"),
  homePrompt: document.querySelector("#home-prompt"),
  chatForm: document.querySelector("#chat-prompt-form"),
  chatPrompt: document.querySelector("#chat-prompt"),
  chatList: document.querySelector("#chat-list"),
  chatContainer: document.querySelector("#chat-container"),
  statusLine: document.querySelector("#status-line"),
  statusText: document.querySelector("#status-text"),
  chatTitle: document.querySelector("#chat-title"),
  chatModelStatic: document.querySelector("#chat-model-static"),
  chatEnergyStatic: document.querySelector("#chat-energy-static"),
  globalEnergy: document.querySelector("#global-energy"),
  routeDetails: document.querySelector("#route-details"),
  energyDetails: document.querySelector("#energy-details"),
  installButton: document.querySelector("#install-button"),
};

let deferredInstallPrompt = null;
let state = loadState();

function loadState() {
  const fallback = { chats: [], activeChatId: null, totals: { usedWh: 0, savedWh: 0 } };
  try { return { ...fallback, ...JSON.parse(localStorage.getItem("seven-web-state") || "{}") }; } catch { return fallback; }
}
function saveState() { localStorage.setItem("seven-web-state", JSON.stringify(state)); }
function sessionKey() { return sessionStorage.getItem("seven-openrouter-key") || ""; }

function classifyQueryType(prompt) {
  if (!prompt.trim()) return { route: "LOCAL", reason: "empty_prompt" };
  const lowered = prompt.toLowerCase();
  const wordCount = prompt.trim().split(/\s+/).length;
  if (REALTIME_KEYWORDS.some((keyword) => lowered.includes(keyword))) return { route: "API_CHECK", reason: "needs_realtime_data" };
  if (SPECIALIZED_DOMAINS.some((domain) => lowered.includes(domain))) return { route: "CLOUD", reason: "specialized_domain" };
  if (COMPLEX_MARKERS.some((marker) => lowered.includes(marker))) return { route: "CLOUD", reason: "too_complex_for_small_model" };
  if (wordCount > 150) return { route: "CLOUD", reason: "prompt_too_long" };
  return { route: "LOCAL", reason: "default_energy_saving" };
}

function resolveRoute(classification) {
  if (classification.route === "LOCAL") return { route: "local", model: LOCAL_MODEL, label: "SEVEN - Local-class", profile: "Ryzen AI / XDNA 2 NPU projection" };
  if (classification.route === "API_CHECK") return { route: "api", model: CLOUD_MODEL, label: "SEVEN - Current-data route", profile: "Direct API precheck + cloud-class summary projection" };
  return { route: "cloud", model: CLOUD_MODEL, label: "SEVEN - Cloud-class", profile: "GPT-4o short prompt cloud baseline projection" };
}

function estimateEnergy(route, tokens) {
  const tokenCount = Math.max(1, tokens || 500);
  const baselineWh = (ENERGY.cloudJPerToken * tokenCount) / ENERGY.joulesPerWh;
  if (route === "local") {
    const actualWh = (ENERGY.localJPerToken * tokenCount) / ENERGY.joulesPerWh;
    return { tokenCount, actualWh, baselineWh, savedWh: baselineWh - actualWh };
  }
  if (route === "api") return { tokenCount, actualWh: ENERGY.apiWh, baselineWh, savedWh: baselineWh - ENERGY.apiWh };
  return { tokenCount, actualWh: baselineWh, baselineWh, savedWh: 0 };
}

function approximateTokens(messages, responseText = "") {
  const text = [...messages.map((message) => message.content), responseText].join(" ");
  return Math.max(80, Math.ceil(text.length / 4));
}
function formatWh(value) {
  if (value >= 1000) return `${(value / 1000).toFixed(2)} kWh`;
  if (value > 0 && value < 0.01) return `${(value * 1000).toFixed(1)} mWh`;
  return `${value.toFixed(2)} Wh`;
}
function titleFromPrompt(prompt) { return prompt.trim().replace(/\s+/g, " ").slice(0, 58) || "Untitled chat"; }
function activeChat() { return state.chats.find((chat) => chat.id === state.activeChatId) || null; }

function createChat(initialPrompt = "") {
  const id = `chat-${Date.now()}`;
  const chat = { id, title: titleFromPrompt(initialPrompt) || "New SEVEN chat", createdAt: new Date().toISOString(), messages: [], energy: { usedWh: 0, savedWh: 0 }, lastRoute: null };
  state.chats.unshift(chat);
  state.activeChatId = id;
  saveState();
  render();
  return chat;
}

function render() {
  const chat = activeChat();
  els.runtimePill.textContent = els.liveToggle.checked && sessionKey() ? "live OpenRouter mode" : "demo mode";
  els.homeScreen.hidden = Boolean(chat);
  els.chatScreen.hidden = !chat;
  els.appShell.dataset.view = chat ? "chat" : "home";
  els.homeButton.classList.toggle("active", !chat);
  renderChatList();
  renderEnergyTotals();
  if (chat) renderChat(chat); else renderRouteDetails(null);
}

function renderChatList() {
  els.chatList.innerHTML = "";
  if (state.chats.length === 0) {
    const empty = document.createElement("p");
    empty.className = "fine-print";
    empty.textContent = "No chats yet.";
    els.chatList.append(empty);
    return;
  }
  for (const chat of state.chats) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = chat.id === state.activeChatId ? "active" : "";
    button.textContent = chat.title;
    button.addEventListener("click", () => { state.activeChatId = chat.id; saveState(); render(); });
    els.chatList.append(button);
  }
}

function renderChat(chat) {
  els.chatTitle.textContent = chat.title;
  els.chatModelStatic.textContent = chat.lastRoute ? `${chat.lastRoute.label} - ${chat.lastRoute.model}` : "Router: local-class first";
  els.chatEnergyStatic.textContent = `${formatWh(chat.energy.usedWh)} used - ${formatWh(chat.energy.savedWh)} saved`;
  els.chatContainer.innerHTML = "";
  for (const message of chat.messages) els.chatContainer.append(renderMessage(message));
  els.chatContainer.scrollTop = els.chatContainer.scrollHeight;
  renderRouteDetails(chat.lastRoute);
}

function renderMessage(message) {
  const box = document.createElement("article");
  box.className = `chatbox ${message.role === "user" ? "user" : "assistant"}`;
  const title = document.createElement("div");
  title.className = "chatbox-title";
  title.textContent = message.role === "user" ? "You" : (message.sourceLabel || "SEVEN");
  const content = document.createElement("div");
  content.className = "chatbox-content";
  content.textContent = message.content;
  box.append(title, content);
  return box;
}

function renderEnergyTotals() {
  const totals = state.chats.reduce((acc, chat) => {
    acc.usedWh += chat.energy.usedWh || 0;
    acc.savedWh += chat.energy.savedWh || 0;
    return acc;
  }, { usedWh: 0, savedWh: 0 });
  state.totals = totals;
  els.globalEnergy.textContent = `${formatWh(totals.usedWh)} used - ${formatWh(totals.savedWh)} saved - ${equivalentText(totals.savedWh)}`;
}
function equivalentText(savedWh) {
  if (savedWh <= 0) return "no routed prompts yet";
  if (savedWh < 1) return `${(savedWh * 1000).toFixed(0)} mWh avoided versus cloud-only`;
  return `${savedWh.toFixed(2)} Wh avoided versus cloud-only`;
}

function renderRouteDetails(route) {
  const safeRoute = route || { route: "none", reason: "waiting", model: "none", energy: { actualWh: 0, baselineWh: 0, savedWh: 0 } };
  const reason = reasonLabels[safeRoute.reason || "waiting"] || safeRoute.reason || "Waiting";
  els.routeDetails.innerHTML = `<div><dt>Selected</dt><dd>${escapeHtml(safeRoute.route)}</dd></div><div><dt>Reason</dt><dd>${escapeHtml(reason)}</dd></div><div><dt>Model</dt><dd>${escapeHtml(safeRoute.model || "none")}</dd></div>`;
  els.energyDetails.innerHTML = `<div><dt>Actual</dt><dd>${formatWh(safeRoute.energy.actualWh)}</dd></div><div><dt>Baseline</dt><dd>${formatWh(safeRoute.energy.baselineWh)}</dd></div><div><dt>Savings</dt><dd>${formatWh(safeRoute.energy.savedWh)}</dd></div>`;
}
function escapeHtml(value) { return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;"); }

async function submitPrompt(prompt) {
  let chat = activeChat();
  if (!chat) chat = createChat(prompt);
  chat.messages.push({ role: "user", content: prompt, timestamp: new Date().toISOString() });
  if (!chat.title || chat.title === "New SEVEN chat" || chat.title === "Untitled chat") chat.title = titleFromPrompt(prompt);
  saveState();
  render();
  setPromptEnabled(false);
  try {
    const result = await routePrompt(chat, prompt);
    chat.messages.push({ role: "assistant", content: result.text, timestamp: new Date().toISOString(), sourceLabel: `${result.label} - Used ${(result.energy.actualWh * 1000).toFixed(1)} mWh` });
    chat.energy.usedWh += result.energy.actualWh;
    chat.energy.savedWh += result.energy.savedWh;
    chat.lastRoute = result;
    saveState();
  } catch (error) {
    chat.messages.push({ role: "assistant", content: `SEVEN routing failed: ${error.message}`, timestamp: new Date().toISOString(), sourceLabel: "SEVEN - Routing error" });
    saveState();
  } finally {
    setStatus("complete", false);
    setPromptEnabled(true);
    render();
  }
}

async function routePrompt(chat, prompt) {
  const classification = classifyQueryType(prompt);
  const target = resolveRoute(classification);
  if (els.liveToggle.checked && !sessionKey()) {
    throw new Error("Live AI mode needs an OpenRouter key. Paste a key, click Save session key, then send again.");
  }
  if (target.route === "api") { setStatus("api_fetching", true); await pause(350); }
  setStatus(target.route === "local" ? "local_starting" : "cloud_processing", true);
  const messages = buildMessages(chat, prompt, target.route);
  const useLive = els.liveToggle.checked && sessionKey();
  const started = performance.now();
  let text;
  let model = target.model;
  if (useLive) {
    const live = await callOpenRouter(messages, modelsForRoute(target.route), sessionKey());
    text = live.text;
    model = live.model || target.model;
  } else {
    await pause(target.route === "local" ? 550 : 900);
    text = demoResponse(prompt, classification, target);
  }
  const latencyS = (performance.now() - started) / 1000;
  const tokens = approximateTokens(messages, text);
  const energy = estimateEnergy(target.route, tokens);
  return { ...target, model, reason: classification.reason, text, latencyS, tokens, energy };
}

function buildMessages(chat, prompt, route) {
  const context = chat.messages.slice(-8).filter((message) => message.role === "user" || message.role === "assistant").map((message) => ({ role: message.role, content: message.content }));
  return [
    { role: "system", content: route === "local" ? "You are SEVEN's concise local-class route. Answer briefly. If the request needs current facts or deep reasoning, state the limitation briefly." : "You are SEVEN's stronger cloud-class route. Be helpful, concise, and mention when current facts would require a live data tool." },
    ...context,
    { role: "user", content: prompt },
  ];
}

function modelsForRoute(route) {
  return route === "local" ? LOCAL_FALLBACK_MODELS : CLOUD_FALLBACK_MODELS;
}

async function callOpenRouter(messages, models, apiKey) {
  const failures = [];
  for (const model of models) {
    const response = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: { "Authorization": `Bearer ${apiKey}`, "Content-Type": "application/json", "HTTP-Referer": window.location.origin, "X-Title": "SEVEN Portfolio Demo" },
      body: JSON.stringify({ model, messages, temperature: 0.3, max_tokens: 700 }),
    });
    if (response.ok) {
      const data = await response.json();
      return { text: data.choices?.[0]?.message?.content?.trim() || "", model: data.model || model };
    }
    const body = await response.text();
    failures.push(`${model}: ${response.status} ${body.slice(0, 160)}`);
    if (!shouldTryNextModel(response.status, body)) break;
  }
  throw new Error(`OpenRouter failed after fallback attempts. ${failures.join(" | ")}`);
}

function shouldTryNextModel(status, body) {
  if (status === 429 || status === 503) return true;
  const lowered = body.toLowerCase();
  return lowered.includes("rate-limit") || lowered.includes("rate limited") || lowered.includes("temporarily") || lowered.includes("no available");
}

function demoResponse(prompt, classification, target) {
  if (target.route === "local") return ["Local-class response:", conciseAnswer(prompt), "", "SEVEN selected the small-model route because the prompt did not trip real-time, specialized-domain, long-form, or length heuristics."].join("\n");
  const reason = reasonLabels[classification.reason] || classification.reason;
  if (target.route === "api") return ["Current-data route response:", "This prompt asks for information that may change over time. In the full SEVEN system, this path performs a direct API check before composing the answer.", "", `Reason: ${reason}.`].join("\n");
  return ["Cloud-class response:", "This request appears complex enough to justify a stronger model. SEVEN escalated rather than spending local-class inference on a likely insufficient answer.", "", `Reason: ${reason}. Prompt preview: "${prompt.slice(0, 140)}"`].join("\n");
}
function conciseAnswer(prompt) {
  const lowered = prompt.toLowerCase();
  if (lowered.includes("2+2") || lowered.includes("2 + 2")) return "2 + 2 = 4.";
  if (lowered.includes("capital of france")) return "The capital of France is Paris.";
  if (lowered.includes("seven")) return "SEVEN is an energy-aware router that chooses between smaller local-class inference and larger cloud-class inference.";
  return "This looks suitable for a short factual response. In live mode, this route calls the small free model selected for the local-class simulation.";
}
function setStatus(status, visible) { els.statusLine.hidden = !visible; els.statusText.textContent = statusLabels[status] || status; }
function setPromptEnabled(enabled) {
  els.homePrompt.disabled = !enabled;
  els.chatPrompt.disabled = !enabled;
  els.homeForm.querySelector("button").disabled = !enabled;
  els.chatForm.querySelector("button").disabled = !enabled;
}
function pause(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
function wireForm(form, textarea) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = textarea.value.trim();
    if (!prompt) return;
    textarea.value = "";
    submitPrompt(prompt);
  });
  textarea.addEventListener("keydown", (event) => {
    const submitShortcut = event.key === "Enter" && !event.shiftKey;
    if (submitShortcut) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
}

els.saveKeyButton.addEventListener("click", () => {
  const value = els.keyInput.value.trim();
  if (value) sessionStorage.setItem("seven-openrouter-key", value);
  els.keyInput.value = "";
  render();
});
els.clearKeyButton.addEventListener("click", () => {
  sessionStorage.removeItem("seven-openrouter-key");
  els.keyInput.value = "";
  els.liveToggle.checked = false;
  render();
});
els.clearChatsButton.addEventListener("click", () => {
  state.chats = [];
  state.activeChatId = null;
  state.totals = { usedWh: 0, savedWh: 0 };
  saveState();
  render();
});
els.liveToggle.addEventListener("change", render);
els.homeButton.addEventListener("click", () => { state.activeChatId = null; saveState(); render(); });
els.closeChatButton.addEventListener("click", () => { state.activeChatId = null; saveState(); render(); });
els.newChatButton.addEventListener("click", () => createChat());
wireForm(els.homeForm, els.homePrompt);
wireForm(els.chatForm, els.chatPrompt);

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  els.installButton.hidden = false;
});
els.installButton.addEventListener("click", async () => {
  if (!deferredInstallPrompt) return;
  deferredInstallPrompt.prompt();
  await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
  els.installButton.hidden = true;
});
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./service-worker.js").then((registration) => {
    registration.update().catch(() => {});
  }).catch(() => {});
}
render();
