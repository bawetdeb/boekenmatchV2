const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  vm = require("node:vm");
const ctx = { window: {} };
ctx.window = ctx;
vm.createContext(ctx);
for (const file of [
  "data/books.js",
  "js/diversification.js",
  "js/matchingEngine.js",
])
  vm.runInContext(fs.readFileSync(file, "utf8"), ctx);
const { BOOKS: books, matchingEngine: engine } = ctx;
const base = {
  level: "kader",
  schoolYear: 3,
  readingMotivation: 3,
  readingDifficulty: 2,
  readingAbility: 2,
  interests: [],
  themes: {
    spanning: 2,
    humor: 2,
    romantiek: 1,
    horror: 0,
    actie: 2,
    emotioneel: 2,
  },
  readingSpeed: 4,
  maxPages: 250,
  realismFantasy: 1,
  avoidTopics: [],
};
const profiles = [
  {
    ...base,
    level: "basis",
    readingMotivation: 1,
    readingDifficulty: 1,
    interests: ["voetbal"],
    primaryInterest: "voetbal",
    storyPreferences: ["spanning", "sport"],
    themes: { ...base.themes, spanning: 5, humor: 1, horror: 0 },
    maxPages: 160,
  },
  {
    ...base,
    interests: ["games", "mysterie"],
    primaryInterest: "games",
    storyPreferences: ["technologie", "mysterie"],
    themes: { ...base.themes, spanning: 5, humor: 0 },
    readingSpeed: 5,
    realismFantasy: 3,
  },
  {
    ...base,
    level: "gt",
    interests: ["oorlog", "geschiedenis"],
    primaryInterest: "oorlog",
    storyPreferences: ["oorlog"],
    themes: { ...base.themes, emotioneel: 4, humor: 0 },
    readingDifficulty: 4,
    readingMotivation: 4,
    readingSpeed: 2,
    maxPages: 400,
  },
  {
    ...base,
    interests: ["verliefdheid", "school"],
    primaryInterest: "verliefdheid",
    storyPreferences: ["romantiek", "school"],
    themes: { ...base.themes, romantiek: 5, emotioneel: 5, humor: 1 },
  },
  {
    ...base,
    level: "basis",
    readingMotivation: 1,
    readingDifficulty: 1,
    interests: ["humor"],
    primaryInterest: "humor",
    storyPreferences: ["humor"],
    themes: { ...base.themes, humor: 5, spanning: 0, horror: 0 },
    maxPages: 180,
  },
];
test("98 distinct titles with complete schema and 40–70 word summaries", () => {
  assert.equal(books.length, 98);
  assert.equal(new Set(books.map((b) => b.id)).size, 98);
  for (const b of books) {
    for (const k of [
      "isbn",
      "coverUrl",
      "auraId",
      "auraUrl",
      "location",
      "ageMin",
      "ageMax",
      "schoolYear",
      "chapterLength",
    ])
      assert.ok(k in b);
    const words = b.summary.split(/\s+/).length;
    assert.ok(words >= 40 && words <= 70, `${b.title}: ${words}`);
    assert.ok(Object.values(b.themes).every((v) => v >= 0 && v <= 5));
  }
});
test("five profiles produce distinct top fives with intended first interests", () => {
  const results = profiles.map((p) => engine.recommend(books, p));
  for (let i = 0; i < results.length; i++) {
    assert.equal(results[i].length, 5);
    assert.ok(results[i][0].interests.includes(profiles[i].primaryInterest));
    console.log(
      i + 1,
      results[i].map((b) => b.title + " (" + b.matchScore + ")").join(" | "),
    );
  }
  assert.equal(
    new Set(results.map((r) => r.map((b) => b.id).join(","))).size,
    5,
  );
});
test("hard exclusions remain hard even when alternatives run out", () => {
  const p = {
    ...base,
    level: "basis",
    avoidTopics: ["dood", "drugs", "geweld"],
  };
  const r = engine.recommend(books, p, 100);
  assert.ok(r.length > 0);
  assert.ok(
    r.every(
      (b) =>
        b.available &&
        b.levels.some((l) => l !== "gt") &&
        !b.sensitiveTopics.some((t) => p.avoidTopics.includes(t)),
    ),
  );
  assert.equal(
    engine.recommend([{ ...books[0], available: false }], p).length,
    0,
  );
  assert.equal(
    engine.recommend([{ ...books[0], levels: ["gt"] }], p).length,
    0,
  );
});
test("diversification keeps first match and distinct authors when possible", () => {
  for (const p of profiles) {
    const r = engine.recommend(books, p);
    const ranked = books
      .filter((b) => engine.eligible(b, p))
      .map((b) => ({ id: b.id, score: engine.scoreBook(b, p) }))
      .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
    assert.equal(r[0].id, ranked[0].id);
    assert.equal(new Set(r.map((b) => b.author)).size, 5);
  }
});
test("five others avoid shown and disliked titles while alternatives exist", () => {
  const p = profiles[1],
    first = engine.recommend(books, p),
    second = engine.recommend(books, p, 5, {
      exclude: first.map((b) => b.id),
      feedback: { [first[0].id]: -1 },
    });
  assert.equal(second.length, 5);
  assert.ok(second.every((b) => !first.some((x) => x.id === b.id)));
});
test("feedback changes similar book scores and primary interest counts double", () => {
  const p = profiles[1];
  engine.recommend(books, p);
  const b = books[0],
    other = books[1];
  assert.ok(
    engine.scoreBook(other, p, { [b.id]: 1 }) >
      engine.scoreBook(other, p, { [b.id]: -1 }),
  );
  const football = books.find((b) => b.interests.includes("voetbal"));
  assert.ok(
    engine.scoreBook(football, {
      ...base,
      interests: ["voetbal", "games"],
      primaryInterest: "voetbal",
    }) >
      engine.scoreBook(football, {
        ...base,
        interests: ["voetbal", "games"],
        primaryInterest: "games",
      }),
  );
});

test("score is normalized to active weight maximum, with transparent breakdown", () => {
  const p = { ...base, storyPreferences: ["mysterie"], readingAbility: 2 };
  const b = books[0];
  const e = engine.evaluate(b, p);
  assert.equal(
    e.matchScore,
    Math.round(
      engine.clamp(
        (100 * (e.weighted + e.combination - e.penalty)) / e.maximum,
        0,
        100,
      ),
    ),
  );
  assert.ok(e.maximum > 0);
  assert.ok(e.parts.themes >= 0 && e.parts.themes <= 1);
});
test("neutral choices omit their preference instead of inventing a middle value", () => {
  const p = {
    ...base,
    readingMotivation: 3,
    readingDifficulty: null,
    readingSpeed: null,
    realismFantasy: null,
    maxPages: null,
  };
  const e = engine.evaluate(books[0], p);
  assert.equal(e.parts.readingStyle, null);
  assert.equal(e.parts.length, null);
  const b = {
    ...books[0],
    readingDifficulty: 5,
    readingSpeed: 1,
    realismFantasy: 5,
    pages: 900,
  };
  assert.equal(engine.evaluate(b, p).parts.mood, e.parts.mood);
});
test("reading ability, dark themes and low motivation produce penalties", () => {
  const b = {
    ...books[0],
    readingDifficulty: 5,
    pages: 520,
    readingSpeed: 1,
    chapterLength: 5,
    narrativeClarity: 1,
    fastStart: 1,
    realismFantasy: 5,
  };
  assert.ok(
    engine.scoreBook(b, {
      ...base,
      readingMotivation: 1,
      readingAbility: 1,
      realismFantasy: 1,
    }) <
      engine.scoreBook(b, {
        ...base,
        readingMotivation: 4,
        readingAbility: 3,
        realismFantasy: 5,
      }),
  );
  const scary = { ...books[0], themes: { ...books[0].themes, horror: 5 } };
  assert.ok(
    engine.scoreBook(scary, { ...base, themes: { horror: 0 } }) <
      engine.scoreBook(scary, { ...base, themes: { horror: 5 } }),
  );
});
test("story preferences and true-story choice affect content scores", () => {
  const diary = books.find((b) => b.title === "Het achterhuis"),
    novel = books.find((b) => b.title === "Oorlogswinter");
  assert.ok(
    engine.evaluate(diary, { ...base, storyPreferences: ["waargebeurd"] }).parts
      .themes >
      engine.evaluate(novel, { ...base, storyPreferences: ["waargebeurd"] })
        .parts.themes,
  );
  assert.ok(
    engine.evaluate(books[0], { ...base, storyPreferences: ["technologie"] })
      .parts.themes >
      engine.evaluate(novel, { ...base, storyPreferences: ["technologie"] })
        .parts.themes,
  );
});
test("language and future Aura membership remain hard requirements", () => {
  assert.equal(engine.recommend(books, { ...base, language: "de" }).length, 0);
  assert.equal(
    engine.recommend(books, base, 5, { requireAura: true }).length,
    0,
  );
  const b = { ...books[0], auraId: "a1", catalogSource: "aura" };
  assert.equal(engine.recommend([b], base, 5, { requireAura: true }).length, 1);
});
test("slight variation preserves first match and is reproducible for equally good alternatives", () => {
  const fixtures = Array.from({ length: 20 }, (_, i) => ({
    ...books[0],
    id: "v" + String(i).padStart(2, "0"),
    author: "Auteur " + i,
  }));
  const a = engine.recommend(fixtures, profiles[1], 5, { seed: 12 }),
    repeat = engine.recommend(fixtures, profiles[1], 5, { seed: 12 });
  assert.deepEqual(
    a.map((b) => b.id),
    repeat.map((b) => b.id),
  );
  const sequences = new Set();
  for (let seed = 1; seed < 20; seed++) {
    const r = engine.recommend(fixtures, profiles[1], 5, { seed });
    assert.equal(r[0].id, a[0].id);
    sequences.add(r.map((b) => b.id).join(","));
  }
  assert.ok(sequences.size > 1);
});
test("prefer seen accepted books over rejected books when new titles run out", () => {
  const set = books.slice(0, 3),
    p = profiles[1];
  const r = engine.recommend(set, p, 2, {
    exclude: set.map((b) => b.id),
    feedback: { [set[0].id]: -1 },
  });
  assert.ok(r.every((b) => b.id !== set[0].id));
});
test("theme diversity allows at most two nearly identical profiles if close alternatives exist", () => {
  const core = books[0];
  const fixtures = Array.from({ length: 8 }, (_, i) => ({
    ...core,
    id: "f" + i,
    author: "a" + i,
    matchScore: 90 - i,
    interests: i < 4 ? ["games"] : i < 6 ? ["sport"] : ["oorlog"],
    themes:
      i < 4
        ? { spanning: 5, mysterie: 5 }
        : i < 6
          ? { humor: 5, sport: 5 - (i % 2) }
          : { oorlog: 5, emotioneel: 4 },
  }));
  const result = ctx.diversification.select(fixtures);
  assert.equal(result[0].id, "f0");
  assert.ok(result.filter((b) => b.interests.includes("games")).length <= 2);
});
