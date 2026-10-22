window.bookRepository = {
  status: { source: "test", checkedAt: null },
  async getBooks() {
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
