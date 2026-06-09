const { test, expect } = require("@playwright/test");
const { execFileSync } = require("node:child_process");

const BASELINE_URL = process.env.BASELINE_PUBLICATIONS_URL;
const APP_URL = process.env.NEW_PUBLICATIONS_URL || readTofuOutput("site_url");

const CASES = [
  {
    name: "default all publications",
    filters: {}
  },
  {
    name: "single data type",
    filters: { dataTypes: ["Fish"] }
  },
  {
    name: "single environmental issue",
    filters: { environmentalIssues: ["Climate Change"] }
  },
  {
    name: "single lake",
    filters: { lakes: ["239"] }
  },
  {
    name: "single author",
    filters: { authors: ["Paterson, M. J."] }
  },
  {
    name: "year range",
    filters: { yearStart: "2020", yearEnd: "2024" }
  },
  {
    name: "general search",
    filters: { generalSearch: "cyanobacteria" }
  },
  {
    name: "author type current researchers",
    filters: { authorType: "Current IISD-ELA researchers" }
  },
  {
    name: "author type supported researchers",
    filters: { authorType: "Other researchers (supported by IISD-ELA)" }
  },
  {
    name: "author type students",
    filters: { authorType: "Students (theses)" }
  },
  {
    name: "combined tags use OR logic",
    filters: {
      dataTypes: ["Hydrology"],
      environmentalIssues: ["Mercury"],
      lakes: ["239"],
      authors: ["Higgins, S."]
    }
  },
  {
    name: "combined filters use narrowing logic",
    filters: {
      dataTypes: ["Fish"],
      environmentalIssues: ["Climate Change"],
      yearStart: "2020",
      yearEnd: "2025",
      generalSearch: "lake"
    }
  },
  {
    name: "multi data type plus author type",
    filters: {
      dataTypes: ["Chemistry", "Fish"],
      authorType: "Current IISD-ELA researchers"
    }
  },
  {
    name: "scientist profile author query",
    filters: { scientistAuthor: "Paterson, M. J." }
  }
];

const BASELINE_WIDGET_NAMES = {
  dataTypes: /data.*types/i,
  environmentalIssues: /environmental.*issues/i,
  lakes: /lakes/i,
  authors: /authors/i,
  authorType: /author.*type/i,
  yearStart: /year.*start/i,
  yearEnd: /year.*end/i,
  generalSearch: /general.*search/i
};

test.describe("publications search", () => {
  for (const testCase of CASES) {
    test(testCase.name, async ({ browser }) => {
      const appPage = await browser.newPage();

      const appResult = await runAppCase(appPage, testCase.filters);

      if (BASELINE_URL) {
        const baselinePage = await browser.newPage();
        const baselineResult = await runBaselineAppCase(baselinePage, testCase.filters);

        if (testCase.filters.scientistAuthor) {
          expect(appResult.firstResult, JSON.stringify({ baselineResult, appResult }, null, 2)).toContain(
            baselineResult.firstResult.slice(0, 40)
          );
        } else {
          expect(appResult.count, JSON.stringify({ baselineResult, appResult }, null, 2)).toBe(baselineResult.count);
        }
        expect(baselineResult.firstResult.length).toBeGreaterThan(20);
        await baselinePage.close();
      } else {
        expect(appResult.count).toBeGreaterThan(0);
      }
      expect(appResult.firstResult.length).toBeGreaterThan(20);

      await appPage.close();
    });
  }
});

async function runBaselineAppCase(page, filters) {
  const url = filters.scientistAuthor
    ? `${BASELINE_URL}?author_tags=${encodeURIComponent(filters.scientistAuthor)}`
    : BASELINE_URL;
  await page.goto(url, { waitUntil: "domcontentloaded" });
  const app = page.frameLocator("iframe").first();
  await waitForBaselineApp(app, filters.scientistAuthor);

  if (!filters.scientistAuthor) {
    await applyBaselineMultiSelect(page, app, BASELINE_WIDGET_NAMES.dataTypes, filters.dataTypes);
    await applyBaselineMultiSelect(page, app, BASELINE_WIDGET_NAMES.environmentalIssues, filters.environmentalIssues);
    await applyBaselineMultiSelect(page, app, BASELINE_WIDGET_NAMES.lakes, filters.lakes);
    await applyBaselineMultiSelect(page, app, BASELINE_WIDGET_NAMES.authors, filters.authors);
    await applyBaselineSelect(app, BASELINE_WIDGET_NAMES.authorType, filters.authorType);
    await applyBaselineTextInput(page, app, BASELINE_WIDGET_NAMES.yearStart, filters.yearStart);
    await applyBaselineTextInput(page, app, BASELINE_WIDGET_NAMES.yearEnd, filters.yearEnd);
    await applyBaselineTextInput(page, app, BASELINE_WIDGET_NAMES.generalSearch, filters.generalSearch);
  }

  await waitForStableBaselineResults(app);
  return readBaselineResults(app, filters.scientistAuthor);
}

async function runAppCase(page, filters) {
  const url = filters.scientistAuthor
    ? `${APP_URL}?author_tags=${encodeURIComponent(filters.scientistAuthor)}`
    : APP_URL;
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await waitForApp(page, filters.scientistAuthor);

  if (!filters.scientistAuthor) {
    await applyNewMultiSelect(page, "#data-type-tags", filters.dataTypes);
    await applyNewMultiSelect(page, "#env-issue-tags", filters.environmentalIssues);
    await applyNewMultiSelect(page, "#lake-tags", filters.lakes);
    await applyNewMultiSelect(page, "#author-tags", filters.authors);
    await applyNewSelect(page, "#author-type", filters.authorType);
    await applyNewTextInput(page, "#year-start", filters.yearStart);
    await applyNewTextInput(page, "#year-end", filters.yearEnd);
    await applyNewTextInput(page, "#general-search", filters.generalSearch);
  }

  await waitForStableAppResults(page, Boolean(filters.scientistAuthor));
  return readAppResults(page, filters.scientistAuthor);
}

async function waitForBaselineApp(page, isScientistProfile) {
  const titlePattern = isScientistProfile ? /Academic Publications by/ : /Search Results \(\d+\)/;
  await expect(page.getByText(titlePattern)).toBeVisible({ timeout: 90000 });
}

async function waitForApp(page, isScientistProfile) {
  if (isScientistProfile) {
    await expect(page.getByText(/Academic Publications by/)).toBeVisible({ timeout: 90000 });
    return;
  }

  await expect(page.locator("#results-title")).toHaveText(/Search Results \(\d+\)/, { timeout: 90000 });
  await expect(page.locator("#author-tags .multi-option").first()).toBeAttached({ timeout: 90000 });
  await page.waitForFunction(
    () => !document.querySelector("#status")?.textContent?.includes("Loading"),
    null,
    { timeout: 90000 }
  );
}

async function applyBaselineMultiSelect(rootPage, app, name, values = []) {
  for (const value of values || []) {
    const combo = app.getByRole("combobox", { name }).first();
    await combo.click();
    await combo.fill(value);
    await app.getByText(value, { exact: true }).last().click();
    await rootPage.keyboard.press("Escape");
    await sleep(200);
  }
}

async function applyBaselineSelect(app, name, value) {
  if (!value) return;
  await app.getByRole("combobox", { name }).first().click();
  await app.getByText(value, { exact: true }).last().click();
}

async function applyBaselineTextInput(rootPage, app, name, value) {
  if (!value) return;
  await app.getByRole("textbox", { name }).first().fill(value);
  await rootPage.keyboard.press("Enter");
  await sleep(200);
}

async function applyNewMultiSelect(page, selector, values = []) {
  for (const value of values || []) {
    const field = page.locator(selector);
    await field.locator(".multi-trigger").click();
    const option = field.locator(".multi-option", { hasText: value }).locator("input");
    await expect(option).toBeAttached({ timeout: 90000 });
    await option.check({ force: true });
    await page.keyboard.press("Escape");
  }
}

async function applyNewSelect(page, selector, value) {
  if (!value) return;
  await expect(page.locator(`${selector} option`, { hasText: value })).toBeAttached({ timeout: 90000 });
  await page.locator(selector).selectOption({ label: value });
}

async function applyNewTextInput(page, selector, value) {
  if (!value) return;
  await page.locator(selector).fill(value);
}

async function waitForStableBaselineResults(page) {
  await sleep(800);
  await expect(page.getByText(/Search Results \(\d+\)|Academic Publications by/).first()).toBeVisible();
}

async function waitForStableAppResults(page, isScientistProfile = false) {
  const statusSelector = isScientistProfile ? "#scientist-status" : "#status";
  if (!isScientistProfile) {
    await page.waitForTimeout(250);
  }
  await page.waitForFunction(
    (selector) => !document.querySelector(selector)?.textContent?.includes("Loading"),
    statusSelector,
    { timeout: 90000 }
  );
  if (isScientistProfile) {
    await expect(page.locator("#scientist-results .result-item").first()).toBeVisible({ timeout: 90000 });
  }
  await page.waitForTimeout(200);
}

async function readBaselineResults(page, isScientistProfile) {
  const count = isScientistProfile
    ? 0
    : parseSearchCount(await page.getByText(/Search Results \(\d+\)/).first().innerText());
  const firstResult = await page.getByText(/\(\d{4}\)\./).first().innerText();
  return { count, firstResult };
}

async function readAppResults(page, isScientistProfile) {
  if (isScientistProfile) {
    const items = page.locator(".result-item");
    const count = await items.count();
    const firstResult = count ? await items.first().innerText() : "";
    return { count, firstResult };
  }

  const heading = await page.locator("#results-title").innerText();
  const count = parseCountFromHeading(heading);
  const firstResult = count ? await page.locator(".result-item").first().innerText() : "";
  return { count, firstResult };
}

function parseSearchCount(text) {
  const match = text.match(/Search Results \((\d+)\)/);
  if (!match) throw new Error(`Could not find search result count in text: ${text.slice(0, 500)}`);
  return Number(match[1]);
}

function parseCountFromHeading(text) {
  const match = text.match(/\((\d+)\)/);
  if (!match) throw new Error(`Could not find count in heading: ${text}`);
  return Number(match[1]);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function readTofuOutput(name) {
  try {
    return execFileSync(
      "tofu",
      ["-chdir=infrastructure/publications", "output", "-raw", name],
      { encoding: "utf8" }
    ).trim();
  } catch (error) {
    throw new Error(
      `Set NEW_PUBLICATIONS_URL or run OpenTofu before tests. Could not read tofu output ${name}.`
    );
  }
}
