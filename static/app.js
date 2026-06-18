const API_BASE = "/api";
const API_RETRY_DELAYS_MS = [600, 1600, 3200];

try {
  if (window.self !== window.top) {
    document.documentElement.classList.add("is-embedded");
  }
} catch (error) {
  document.documentElement.classList.add("is-embedded");
}

const SELECTS = {
  data_type_tags: document.getElementById("data-type-tags"),
  env_issue_tags: document.getElementById("env-issue-tags"),
  lake_tags: document.getElementById("lake-tags"),
  author_tags: document.getElementById("author-tags"),
};

const authorType = document.getElementById("author-type");
const yearStart = document.getElementById("year-start");
const yearEnd = document.getElementById("year-end");
const generalSearch = document.getElementById("general-search");
const clearSearch = document.getElementById("clear-search");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const resultsTitle = document.getElementById("results-title");
const yearRangeEl = document.getElementById("year-range");

const searchView = document.getElementById("search-view");
const scientistView = document.getElementById("scientist-view");
const scientistTitle = document.getElementById("scientist-title");
const scientistStatus = document.getElementById("scientist-status");
const scientistResults = document.getElementById("scientist-results");
const scientistDisclaimer = document.getElementById("scientist-disclaimer");

let debounceTimer;
let searchRequestId = 0;
const dropdowns = new Map();

document.addEventListener("DOMContentLoaded", init);
document.addEventListener("click", closeDropdownsOnOutsideClick);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeAllDropdowns();
});

async function init() {
  const query = new URLSearchParams(window.location.search);
  const scientist = normalizeAuthorParam(query.get("author_tags"));

  if (scientist) {
    searchView.hidden = true;
    scientistView.hidden = false;
    await renderScientist(scientist);
    return;
  }

  searchView.hidden = false;
  scientistView.hidden = true;
  try {
    await loadOptions();
    wireInputs();
    await runSearch();
  } catch (error) {
    setStatus("Could not load publications data. Please try again.", true);
  }
}

async function loadOptions() {
  setStatus("Loading publications data...");
  const options = await getJson(`${API_BASE}/options`);
  fillMultiSelect(SELECTS.data_type_tags, options.data_types);
  fillMultiSelect(SELECTS.env_issue_tags, options.environmental_issues);
  fillMultiSelect(SELECTS.lake_tags, options.lakes);
  fillMultiSelect(SELECTS.author_tags, options.authors);
  fillSelect(authorType, options.author_type_options);
  yearRangeEl.textContent = `Current year range: ${options.year_range.min}-${options.year_range.max}`;
}

function wireInputs() {
  authorType.addEventListener("change", queueSearch);
  yearStart.addEventListener("input", queueSearch);
  yearEnd.addEventListener("input", queueSearch);
  generalSearch.addEventListener("input", queueSearch);
  clearSearch.addEventListener("click", async () => {
    for (const dropdown of dropdowns.values()) {
      for (const input of dropdown.inputs) input.checked = false;
      updateMultiSelectLabel(dropdown);
    }
    authorType.selectedIndex = 0;
    yearStart.value = "";
    yearEnd.value = "";
    generalSearch.value = "";
    await runSearch();
  });
}

function queueSearch() {
  window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(runSearch, 180);
}

async function runSearch() {
  const requestId = ++searchRequestId;
  const params = new URLSearchParams();
  appendSelected(params, "data_type_tags", SELECTS.data_type_tags);
  appendSelected(params, "env_issue_tags", SELECTS.env_issue_tags);
  appendSelected(params, "lake_tags", SELECTS.lake_tags);
  appendSelected(params, "author_tags", SELECTS.author_tags);

  if (authorType.value && authorType.value !== "<select a filter>") {
    params.set("author_type", authorType.value);
  }
  if (yearStart.value.trim()) params.set("year_start", yearStart.value.trim());
  if (yearEnd.value.trim()) params.set("year_end", yearEnd.value.trim());
  if (generalSearch.value.trim()) {
    params.set("general_search", generalSearch.value.trim());
  }

  setStatus("Loading...");
  try {
    const payload = await getJson(`${API_BASE}/search?${params}`);
    if (requestId !== searchRequestId) return;
    resultsTitle.textContent = `Search Results (${payload.count})`;
    renderResults(resultsEl, payload.results);
    setStatus(payload.count === 0 ? "No publications were found for your search." : "");
  } catch (error) {
    if (requestId !== searchRequestId) return;
    setStatus("Search failed. Please try again.", true);
  }
}

async function renderScientist(author) {
  author = normalizeAuthorParam(author);
  scientistTitle.textContent = `Academic Publications by ${author}`;
  scientistStatus.textContent = "Loading...";
  scientistStatus.classList.remove("error");
  scientistResults.innerHTML = "";
  scientistDisclaimer.innerHTML = "";

  const params = new URLSearchParams();
  params.append("author_tags", author);
  try {
    const payload = await getJson(`${API_BASE}/search?${params}`);
    renderResults(scientistResults, payload.results);
    scientistStatus.textContent =
      payload.count === 0 ? "No publications were found for your search." : "";
    scientistDisclaimer.innerHTML =
      `Due to ongoing improvements in our <a href="https://www.iisd.org/ela/researchers/publications/">publications database</a>, ` +
      `the list of publications for ${escapeHtml(author)} may not be complete.`;
  } catch (error) {
    scientistStatus.textContent = "Search failed. Please try again.";
    scientistStatus.classList.add("error");
  }
}

function renderResults(container, results) {
  container.innerHTML = "";
  const fragment = document.createDocumentFragment();
  for (const result of results) {
    const item = document.createElement("article");
    item.className = "result-item";

    const citation = document.createElement("div");
    citation.className = "citation";
    citation.innerHTML = result.citation_html;

    const info = document.createElement("button");
    info.className = "info-button";
    info.type = "button";
    info.textContent = "?";
    info.title = result.tag_info;
    info.setAttribute("aria-label", result.tag_info);

    item.append(citation, info);
    fragment.appendChild(item);
  }
  container.appendChild(fragment);
}

async function getJson(url) {
  let lastError;
  for (let attempt = 0; attempt <= API_RETRY_DELAYS_MS.length; attempt += 1) {
    try {
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        const error = new Error(`Request failed with ${response.status}`);
        error.status = response.status;
        throw error;
      }
      return response.json();
    } catch (error) {
      lastError = error;
      const isRetryable = !error.status || error.status === 408 || error.status === 429 || error.status >= 500;
      if (!isRetryable || attempt === API_RETRY_DELAYS_MS.length) break;
      await sleep(API_RETRY_DELAYS_MS[attempt]);
    }
  }
  throw lastError;
}

function normalizeAuthorParam(value) {
  return String(value || "").trim().replace(/;+$/g, "").trim();
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function fillSelect(select, values) {
  select.innerHTML = "";
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}

function fillMultiSelect(container, values) {
  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "multi-trigger";
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");

  const label = document.createElement("span");
  label.className = "multi-label";
  label.textContent = "Choose an option";

  const chevron = document.createElement("span");
  chevron.className = "multi-chevron";
  chevron.setAttribute("aria-hidden", "true");
  chevron.textContent = "⌄";

  const menu = document.createElement("div");
  menu.className = "multi-menu";
  menu.hidden = true;

  const inputs = [];
  values.forEach((value, index) => {
    const option = document.createElement("label");
    option.className = "multi-option";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = value;
    checkbox.id = `${container.id}-${index}`;
    checkbox.addEventListener("change", () => {
      updateMultiSelectLabel(dropdown);
      queueSearch();
    });

    const text = document.createElement("span");
    text.textContent = value;

    option.append(checkbox, text);
    menu.appendChild(option);
    inputs.push(checkbox);
  });

  trigger.append(label, chevron);
  container.replaceChildren(trigger, menu);

  const dropdown = { container, trigger, label, menu, inputs };
  dropdowns.set(container, dropdown);
  updateMultiSelectLabel(dropdown);

  trigger.addEventListener("click", () => toggleDropdown(dropdown));
}

function appendSelected(params, key, select) {
  const dropdown = dropdowns.get(select);
  if (!dropdown) return;
  for (const input of dropdown.inputs) {
    if (input.checked) params.append(key, input.value);
  }
}

function toggleDropdown(dropdown) {
  const shouldOpen = dropdown.menu.hidden;
  closeAllDropdowns(dropdown);
  dropdown.menu.hidden = !shouldOpen;
  dropdown.trigger.setAttribute("aria-expanded", String(shouldOpen));
}

function closeAllDropdowns(exceptDropdown = null) {
  for (const dropdown of dropdowns.values()) {
    if (dropdown === exceptDropdown) continue;
    dropdown.menu.hidden = true;
    dropdown.trigger.setAttribute("aria-expanded", "false");
  }
}

function closeDropdownsOnOutsideClick(event) {
  for (const dropdown of dropdowns.values()) {
    if (dropdown.container.contains(event.target)) return;
  }
  closeAllDropdowns();
}

function updateMultiSelectLabel(dropdown) {
  const selected = dropdown.inputs
    .filter((input) => input.checked)
    .map((input) => input.value);

  dropdown.trigger.classList.toggle("has-selection", selected.length > 0);
  if (selected.length === 0) {
    dropdown.label.textContent = "Choose an option";
  } else if (selected.length === 1) {
    dropdown.label.textContent = selected[0];
  } else {
    dropdown.label.textContent = `${selected.length} selected`;
  }
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}
