module.exports = {
  testDir: "./tests",
  timeout: 120000,
  expect: {
    timeout: 30000
  },
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    browserName: "chromium",
    headless: true,
    viewport: { width: 1600, height: 900 },
    actionTimeout: 30000,
    navigationTimeout: 90000,
    trace: "retain-on-failure"
  }
};
