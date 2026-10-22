const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const read = (file) => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const c = {structuredClone, URL, fetch: async (file) => ({ok: true, json: async () => read(file)})};
c.window = c;
vm.createContext(c);
for (const file of ['data/books.js', 'data/aura-catalog.js', 'js/questions.js', 'js/bookRepository.js', 'js/diversification.js', 'js/matchingEngine.js'])
  vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), c);
(async () => {
  const manifest = read('data/cover-catalog.json');
  assert.equal(manifest.complete, true);
  const books = await c.bookRepository.getBooks({includeUnreviewed: true});
  const interests = Object.values(c.quizConfig.groups).flat();
  const storyPreferences = c.quizConfig.questions.find((q) => q.key === 'storyPreferences').options.map(([key]) => key);
  const eligible = books.filter((b) => ['basis', 'kader', 'gt'].some((level) => c.matchingEngine.eligible(b, {level, interests, storyPreferences, avoidTopics: []})));
  const withCover = (rows) => rows.filter((b) => b.catalogCover);
  const old = read('data/enrichment-report.json');
  const review = read('data/cover-review.json');
  const report = {...manifest.report,
    allAppBooksWithLocalCover: withCover(books).length,
    recommendableBooks: eligible.length,
    recommendableBooksWithLocalCover: withCover(eligible).length,
    recommendableExcelRowsWithLocalCover: withCover(eligible).reduce((sum, b) => sum + b.excelSources.length, 0),
    localImageCount: new Set(Object.values(manifest.records).flatMap((r) => r.covers.map((c) => c.sha256))).size,
    quarantinedImageHashesReviewed: review.quarantinedImageHashes.length,
    visuallyApprovedWorks: review.approved.length,
    visuallyRejectedSourceImages: review.rejected.length,
    editionNote: 'Covers are attached to matched title/author catalog records; the physical Excel edition remains unverified. Open Library covers are illustrative.',
    profiles: old.profiles.map((profile) => ({profile: profile.profile,
      books: profile.topFive.map((entry) => {const b = books.find((book) => book.id === entry.id); return {id: entry.id, title: entry.title, localCover: b?.catalogCover?.url || null};})}))};
  fs.writeFileSync(path.join(root, 'data/cover-report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
})().catch((error) => {console.error(error); process.exitCode = 1;});
