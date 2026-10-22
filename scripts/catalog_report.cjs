// Offline reproducible counts and representative recommendations.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const read = (file) => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const source = read('data/library-catalog.json');
const enriched = read('data/enriched-catalog.json');
const c = { structuredClone, URL, fetch: async (file) => ({ ok: true, json: async () => read(file) }) };
c.window = c;
vm.createContext(c);
for (const file of ['data/books.js', 'data/aura-catalog.js', 'js/questions.js', 'js/bookRepository.js', 'js/diversification.js', 'js/matchingEngine.js'])
  vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), c);

(async () => {
  assert.equal(enriched.recordCount, source.recordCount, 'Every Excel row must have a recorded enrichment attempt');
  assert.equal(enriched.sourceSha256, source.sourceSha256);
  assert.equal(new Set(enriched.records.map((r) => r.id)).size, source.recordCount);
  const books = await c.bookRepository.getBooks({ includeUnreviewed: true });
  assert.equal(books.flatMap((b) => b.excelSources).length, source.recordCount);
  const base = { level: 'kader', schoolYear: 3, readingMotivation: 3, readingAbility: 2,
    readingDifficulty: null, readingSpeed: null, maxPages: null, realismFantasy: null,
    avoidTopics: [], themes: {}, storyPreferences: [] };
  const profiles = [
    { ...base, name: 'Basis / voetbal / spanning / weinig motivatie', level: 'basis', readingMotivation: 1,
      interests: ['voetbal'], primaryInterest: 'voetbal', storyPreferences: ['sport', 'spanning'], maxPages: 160 },
    { ...base, name: 'Kader / games / mysterie', interests: ['games'], primaryInterest: 'games', storyPreferences: ['mysterie', 'technologie'] },
    { ...base, name: 'GT / oorlog / geschiedenis', level: 'gt', readingDifficulty: 4,
      interests: ['oorlog', 'geschiedenis'], primaryInterest: 'oorlog', storyPreferences: ['oorlog'] },
    { ...base, name: 'Kader / liefde / school', interests: ['verliefdheid', 'school'], primaryInterest: 'verliefdheid', storyPreferences: ['romantiek', 'school'] },
    { ...base, name: 'Basis / humor / weinig motivatie', level: 'basis', readingMotivation: 1,
      interests: ['vriendschap'], primaryInterest: 'vriendschap', storyPreferences: ['humor'] },
  ];
  const interests = Object.values(c.quizConfig.groups).flat();
  const stories = c.quizConfig.questions.find((q) => q.key === 'storyPreferences').options.map(([key]) => key);
  const canRecommend = (b) => ['basis', 'kader', 'gt'].some((level) => c.matchingEngine.eligible(b,
    { ...base, level, interests, storyPreferences: stories }));
  const recommendable = books.filter(canRecommend);
  const outcomes = profiles.map((profile) => {
    const top = c.matchingEngine.recommend(books, profile);
    const onlineBooks = books.filter((b) => b.matchMode === 'evidence');
    const onlineTop = c.matchingEngine.recommend(onlineBooks, profile);
    assert.equal(top.length, 5, profile.name);
    assert.equal(onlineTop.length, 5, profile.name + ' (online Excel only)');
    assert.ok([...top, ...onlineTop].every((b) => Number.isFinite(b.matchScore)));
    assert.ok(onlineTop.every((b) => b.levels === null && b.available === null));
    return { profile: profile.name, eligibleOnlineBooks: onlineBooks.filter((b) => c.matchingEngine.eligible(b, profile)).length,
      topFive: top.map((b) => ({ id: b.id, title: b.title, source: b.catalogSource, scoreKind: b.matchMode === 'evidence' ? 'evidence-ranking-no-percentage' : 'legacy-editorial-percentage' })),
      onlineOnlyTopFive: onlineTop.map((b) => ({ id: b.id, title: b.title })) };
  });
  assert.equal(new Set(outcomes.map((r) => r.onlineOnlyTopFive.map((b) => b.id).join('|'))).size, 5);
  const count = (condition) => enriched.records.filter(condition).length;
  const report = {
    sourceSha256: source.sourceSha256, ruleVersion: enriched.ruleVersion,
    sourceRecordCount: source.recordCount, processed: enriched.recordCount,
    fullyEnriched: count((r) => r.status === 'full'),
    partiallyEnriched: count((r) => r.status === 'partial'),
    notEnriched: count((r) => r.status === 'unresolved'),
    definitionFull: 'Verified Excel edition plus ISBN, pages, description, language and supported reading/content assessments. No edition can be identified from title/author alone.',
    definitionPartial: 'At least one additional source fact or supported assessment; other dimensions remain unknown.',
    matchedSourceRecords: count((r) => r.sources.length > 0),
    onlineRecommendationReadyRows: count((r) => r.recommendationReady),
    recommendableExcelRowsIncludingLegacy: recommendable.reduce((sum, b) => sum + b.excelSources.length, 0),
    recommendableUniqueBooksIncludingLegacy: recommendable.length,
    combinedDatabaseRecords: books.length,
    editionVerified: count((r) => r.editionVerified),
    factCoverage: Object.fromEntries(['summary', 'subjects', 'language', 'isbn', 'pages', 'coverUrl', 'available', 'auraId'].map((key) => [key, count((r) => !!r.facts[key])])),
    providers: Object.fromEntries([...new Set(enriched.records.flatMap((r) => r.sources.map((s) => s.provider)))].map((provider) => [provider, count((r) => r.sources.some((s) => s.provider === provider))])),
    recordsWithConflicts: count((r) => r.conflicts.length > 0),
    profiles: outcomes,
  };
  fs.writeFileSync(path.join(root, 'data/enrichment-report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ ...report, profiles: outcomes.map((o) => ({ profile: o.profile, eligibleOnlineBooks: o.eligibleOnlineBooks, topFive: o.topFive.map((b) => b.title) })) }, null, 2));
})().catch((error) => { console.error(error); process.exitCode = 1; });
