const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm"),
  fs = require("node:fs");
function context() {
  const c = { window: null, structuredClone, URL };
  c.window = c;
  vm.createContext(c);
  for (const f of [
    "data/books.js",
    "data/aura-catalog.js",
    "js/bookRepository.js",
    "js/diversification.js",
    "js/matchingEngine.js",
  ])
    vm.runInContext(fs.readFileSync(f, "utf8"), c);
  return c;
}
test("recommendations use confirmed school members and exclude unavailable copies", async () => {
  const c = context(),
    books = await c.bookRepository.getBooks();
  assert.equal(c.bookRepository.status.source, "aura");
  assert.ok(books.length > 5);
  assert.equal(books.length, c.AURA_CATALOG.records.length);
  assert.ok(
    books.every(
      (b) => b.catalogSource === "aura" && b.auraId && b.catalogCheckedAt,
    ),
  );
  const profile = {
    level: "kader",
    schoolYear: 2,
    readingMotivation: 2,
    readingAbility: 2,
    readingDifficulty: 2,
    interests: ["voetbal"],
    primaryInterest: "voetbal",
    themes: { spanning: 4 },
    storyPreferences: ["sport"],
    realismFantasy: null,
    readingSpeed: null,
    maxPages: null,
    avoidTopics: [],
  };
  const matches = c.matchingEngine.recommend(books, profile);
  assert.equal(matches.length, 5);
  assert.ok(
    matches.every(
      (b) => b.available && books.some((x) => x.auraId === b.auraId),
    ),
  );
});
test("missing ISBN, availability, location or deep link is not invented", async () => {
  const c = context();
  c.AURA_CATALOG.records = [
    {
      id: "b001",
      title: "Boy 7",
      auraId: "06326",
      auraUrl: "",
      isbn: "",
      available: false,
      location: "",
      copies: [],
    },
  ];
  const books = await c.bookRepository.getBooks();
  assert.equal(books.length, 1);
  assert.equal(books[0].available, false);
  assert.equal(books[0].isbn, "");
  assert.equal(books[0].auraUrl, "");
  assert.equal(books[0].location, "");
});
test("malformed snapshot fails instead of silently recommending all test books", async () => {
  const c = context();
  c.AURA_CATALOG.records = null;
  await assert.rejects(() => c.bookRepository.getBooks(), /Ongeldige/);
});
test("unknown seed IDs and unsafe record links are excluded", async () => {
  const c = context();
  c.AURA_CATALOG.records = [
    {
      id: "missing",
      auraId: "1",
      auraUrl: "https://bogerman.auralibrary.nl/a",
      available: true,
    },
    {
      id: "b001",
      auraId: "1",
      auraUrl: "https://example.org/a",
      available: true,
    },
  ];
  assert.equal((await c.bookRepository.getBooks()).length, 0);
});
