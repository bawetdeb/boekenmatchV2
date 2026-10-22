const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const c = {}; c.window = c; vm.createContext(c);
for (const file of ['js/diversification.js', 'js/matchingEngine.js']) vm.runInContext(fs.readFileSync(file, 'utf8'), c);
const book = { id: 'partial-1', title: 'Bronboek', author: 'Auteur', matchMode: 'evidence',
  recommendationReady: true, interests: ['voetbal'], storyTags: ['sport'], themes: {},
  levels: null, sensitiveTopics: null, available: null, language: null,
  readingDifficulty: null, pages: null, readingSpeed: null };
const profile = { level: 'basis', interests: ['voetbal'], primaryInterest: 'voetbal',
  storyPreferences: ['sport'], themes: { spanning: 5, humor: 0 }, avoidTopics: [],
  readingDifficulty: 1, readingMotivation: 1, maxPages: 150, schoolYear: 1 };
test('unknown levels, intensity, reading difficulty and pages never become zero or a percentage', () => {
  assert.equal(c.matchingEngine.eligible(book, profile), true);
  const score = c.matchingEngine.evaluate(book, profile);
  assert.ok(Number.isFinite(score.matchScore));
  assert.equal(score.matchPercentage, null);
  for (const field of ['level', 'readingStyle', 'length', 'mood']) assert.equal(score.parts[field], null);
  const changed = { ...profile, readingDifficulty: 5, maxPages: 900, themes: { spanning: 0, humor: 5 } };
  assert.equal(c.matchingEngine.scoreBook(book, profile), c.matchingEngine.scoreBook(book, changed));
  assert.ok(!c.matchingEngine.reasons(book, profile).some((r) => /Past bij jouw niveau|Toegankelijk/.test(r)));
});
test('partial books need positive evidence and respect hard filters conservatively', () => {
  assert.equal(c.matchingEngine.recommend([book], profile).length, 1);
  assert.equal(c.matchingEngine.recommend([book], { ...profile, interests: ['magie'], storyPreferences: [] }).length, 0);
  assert.equal(c.matchingEngine.recommend([{ ...book, available: false }], profile).length, 0);
  assert.equal(c.matchingEngine.recommend([book], { ...profile, avoidTopics: ['geweld'] }).length, 0);
  assert.equal(c.matchingEngine.recommend([book], { ...profile, language: 'nl' }).length, 0);
  assert.equal(c.matchingEngine.recommend([book], profile, 5, { requireAura: true }).length, 0);
});
test('primary interest and feedback influence partial rankings without asserting absent themes', () => {
  assert.ok(c.matchingEngine.scoreBook(book, profile) > c.matchingEngine.scoreBook(book, { ...profile, primaryInterest: 'magie' }));
  c.matchingEngine.books = [book];
  assert.ok(c.matchingEngine.scoreBook(book, profile, { [book.id]: 1 }) > c.matchingEngine.scoreBook(book, profile, { [book.id]: -1 }));
  assert.ok(Number.isFinite(c.diversification.similarity(book, { ...book, themes: null, interests: [] })));
});
