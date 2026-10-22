const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function context(catalog = JSON.parse(fs.readFileSync('data/library-catalog.json', 'utf8'))) {
  const online = JSON.parse(fs.readFileSync('data/enriched-catalog.json', 'utf8'));
  const c = { structuredClone, URL, fetch: async (url) => ({ ok: true, json: async () => structuredClone(url.includes('enriched-catalog') ? online : catalog) }) };
  c.window = c;
  vm.createContext(c);
  for (const file of ['data/books.js', 'data/aura-catalog.js', 'js/bookRepository.js', 'js/diversification.js', 'js/matchingEngine.js'])
    vm.runInContext(fs.readFileSync(file, 'utf8'), c);
  return c;
}
test('live database preserves every Excel row and original unknowns', async () => {
  const c = context();
  const books = await c.bookRepository.getBooks({ includeUnreviewed: true });
  const sources = books.flatMap((b) => Array.from(b.excelSources));
  assert.equal(sources.length, 1529);
  assert.equal(new Set(sources.map((b) => b.id)).size, 1529);
  assert.equal(c.bookRepository.status.excelCount, 1529);
  assert.ok(c.bookRepository.status.linkedExcelCount > 0);
  for (const b of books.filter((b) => b.catalogSource === 'excel')) {
    assert.equal(b.available, null);
    assert.equal(b.excelSources[0].summary, null);
    if (!b.recommendationReady) {
      assert.equal(b.summary, null);
      assert.equal(b.levels, null);
      assert.equal(c.matchingEngine.eligible(b, { level: 'basis' }), false);
    } else if (b.matchMode === 'evidence') {
      assert.ok(b.enrichment.sources.length);
      assert.equal(b.summary, b.enrichment.facts.summary.value);
      assert.equal(b.levels, null);
      assert.deepEqual(Object.keys(b.themes), []);
    } else {
      const original = c.BOOKS.find((x) => x.id === b.metadataSource.id);
      assert.equal(b.summary, original.summary);
      assert.deepEqual(Array.from(b.levels), Array.from(original.levels));
    }
  }
  console.log(`Database: ${books.length} records; ${c.bookRepository.status.linkedExcelCount} linked Excel rows; ${c.bookRepository.status.pendingExcelCount} pending`);
});
test('catalog is actually used in matching without scoring incomplete books', async () => {
  const c = context();
  const books = await c.bookRepository.getBooks({ includeUnreviewed: true });
  const profile = { level: 'kader', schoolYear: 2, readingMotivation: 2, readingAbility: 2,
    interests: ['voetbal'], primaryInterest: 'voetbal', themes: { spanning: 4 },
    storyPreferences: ['sport'], avoidTopics: [] };
  const matches = c.matchingEngine.recommend(books, profile);
  assert.equal(matches.length, 5);
  assert.ok(matches.every((b) => Number.isFinite(b.matchScore) && b.recommendationReady !== false));
  const added = books.filter((b) => b.catalogSource === 'excel' && b.recommendationReady);
  assert.ok(added.length > 0);
  assert.ok(added.some((b) => c.matchingEngine.recommend([b], profile).length === 1));
});
test('similar titles, different authors and ambiguous matches are never merged', async () => {
  const c = context();
  const original = await c.bookRepository.getVerifiedBooks();
  const known = original[0];
  const records = [
    { id: 'one', title: known.title, author: 'Een andere auteur', source: {}, available: null },
    { id: 'two', title: known.title + ' vervolg', author: known.author, source: {}, available: null },
  ];
  c.fetch = async (url) => ({ ok: true, json: async () => url.includes('enriched-catalog') ?
    { schemaVersion: 1, recordCount: 0, records: [] } : { source: 'excel', recordCount: 2, records } });
  const books = await c.bookRepository.getBooks({ includeUnreviewed: true });
  assert.equal(c.bookRepository.status.linkedExcelCount, 0);
  assert.equal(books.length, original.length + 2);
});
test('failed or malformed Excel import fails visibly instead of hiding missing data', async () => {
  const c = context({ source: 'excel', recordCount: 1529, records: [] });
  await assert.rejects(c.bookRepository.getBooks({ includeUnreviewed: true }), /Ongeldige Excel/);
  c.fetch = async () => ({ ok: false });
  await assert.rejects(c.bookRepository.getBooks({ includeUnreviewed: true }), /niet worden geladen/);
});
