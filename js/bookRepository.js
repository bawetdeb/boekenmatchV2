window.bookRepository = {
  status: { source: "test", checkedAt: null },
  async getBooks(options = {}) {
    const verified = await this.getVerifiedBooks();
    if (!options.includeUnreviewed) return verified;
    const response = await fetch("data/library-catalog.json");
    if (!response.ok) throw new Error("De Excelcatalogus kon niet worden geladen");
    const catalog = await response.json();
    if (catalog.source !== "excel" || !Array.isArray(catalog.records) ||
        catalog.recordCount !== catalog.records.length ||
        new Set(catalog.records.map((b) => b.id)).size !== catalog.records.length ||
        catalog.records.some((b) => !b.id || !b.source || typeof b.title !== "string" || typeof b.author !== "string"))
      throw new Error("Ongeldige Excelcatalogus");
    // Only exact title and full author matches (allowing surname-first notation).
    // No fuzzy matching: similar titles and different editions remain separate.
    const normalize = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
    const key = (b) => normalize(b.title) + "|" + normalize(b.author).split(/\s+/).sort().join(" ");
    const candidates = new Map();
    for (const b of verified) {
      const k = key(b);
      candidates.set(k, [...(candidates.get(k) || []), b]);
    }
    const books = verified.map((b) => ({ ...b, excelSources: [] }));
    const byId = new Map(books.map((b) => [b.id, b]));
    const editorial = new Map();
    for (const b of window.BOOKS || []) {
      const k = key(b);
      editorial.set(k, [...(editorial.get(k) || []), b]);
    }
    const enriched = new Map();
    let linked = 0, enrichedRows = 0;
    for (const source of catalog.records) {
      const matches = candidates.get(key(source)) || [];
      if (matches.length === 1) {
        const book = byId.get(matches[0].id);
        book.excelSources.push(structuredClone(source));
        linked++;
      } else {
        const known = editorial.get(key(source)) || [];
        if (known.length === 1) {
          // Reuse existing editorial descriptions, never infer them from C/D.
          const k = key(source);
          if (enriched.has(k)) {
            enriched.get(k).excelSources.push(structuredClone(source));
          } else {
            const book = { ...structuredClone(known[0]),
              id: source.id, title: source.title, author: source.author,
              isbn: null, auraId: null, auraUrl: null, coverUrl: null,
              location: null, available: null, catalogLevel: source.catalogLevel,
              catalogSource: "excel", metadataStatus: "editorial",
              metadataSource: { file: "data/books.js", id: known[0].id },
              recommendationReady: true, excelSources: [structuredClone(source)] };
            books.push(book);
            enriched.set(k, book);
          }
          enrichedRows++;
          continue;
        }
        // Keep unknown values intact; these records can be searched, not scored.
        books.push({ ...structuredClone(source), recommendationReady: false,
          catalogSource: "excel", excelSources: [structuredClone(source)] });
      }
    }
    this.status.excelCount = catalog.records.length;
    this.status.linkedExcelCount = linked;
    this.status.enrichedExcelCount = enrichedRows;
    this.status.pendingExcelCount = catalog.records.length - linked - enrichedRows;
    this.status.verifiedCount = verified.length;
    return books;
  },
  async getVerifiedBooks() {
    const snapshot = window.AURA_CATALOG;
    const seed = window.BOOKS || [];
    if (!snapshot) {
      this.status = { source: "test", checkedAt: null };
      return seed.map((b) => structuredClone(b));
    }
    if (
      snapshot.source !== "aura" ||
      !Array.isArray(snapshot.records) ||
      !snapshot.checkedAt
    )
      throw new Error("Ongeldige Aura-catalogussnapshot");
    this.status = {
      source: "aura",
      checkedAt: snapshot.checkedAt,
      candidateCount: snapshot.candidateCount,
      recordCount: snapshot.records.length,
    };
    return snapshot.records.flatMap((record) => {
      const book = seed.find((b) => b.id === record.id);
      if (!book || !record.auraId || typeof record.available !== "boolean")
        return [];
      try {
        if (record.auraUrl) {
          const u = new URL(record.auraUrl);
          if (
            u.protocol !== "https:" ||
            u.hostname !== "bogerman.auralibrary.nl"
          )
            return [];
        }
      } catch {
        return [];
      }
      return [
        {
          ...structuredClone(book),
          ...structuredClone(record),
          author: book.author,
          catalogSource: "aura",
          catalogCheckedAt: snapshot.checkedAt,
          metadataStatus: "editorial",
        },
      ];
    });
  },
};
