window.diversification = {
  similarity(a, b) {
    const keys = [
      ...new Set([...Object.keys(a.themes), ...Object.keys(b.themes)]),
    ];
    let dot = 0,
      left = 0,
      right = 0;
    for (const k of keys) {
      const x = a.themes[k] || 0,
        y = b.themes[k] || 0;
      dot += x * y;
      left += x * x;
      right += y * y;
    }
    const cosine = left && right ? dot / Math.sqrt(left * right) : 0;
    const union = new Set([...a.interests, ...b.interests]);
    const overlap =
      a.interests.filter((i) => b.interests.includes(i)).length /
      Math.max(1, union.size);
    return 0.7 * cosine + 0.3 * overlap;
  },
  noise(id, seed) {
    let n = seed | 0;
    for (const c of id) n = Math.imul(n ^ c.charCodeAt(0), 16777619);
    n = Math.imul(n ^ (n >>> 16), 2246822507);
    n = Math.imul(n ^ (n >>> 13), 3266489909);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
  },
  select(ranked, limit = 5, options = {}) {
    if (!ranked.length || limit <= 0) return [];
    // Keep number one; diversify in the top 20, extending only for author coverage.
    const candidates = ranked.slice(0, 20);
    for (const b of ranked.slice(20)) {
      if (new Set(candidates.map((x) => x.author)).size >= limit) break;
      if (!candidates.some((x) => x.author === b.author)) candidates.push(b);
    }
    const result = [ranked[0]],
      remaining = candidates.filter((b) => b.id !== ranked[0].id);
    while (result.length < limit && remaining.length) {
      const tier = Math.min(...remaining.map((b) => b.noveltyTier ?? 0));
      const tierPool = remaining.filter((b) => (b.noveltyTier ?? 0) === tier);
      const distinct = tierPool.filter(
        (b) => !result.some((r) => r.author === b.author),
      );
      const authors = distinct.length ? distinct : tierPool;
      const varied = authors.filter(
        (b) => result.filter((r) => this.similarity(b, r) >= 0.9).length < 2,
      );
      const best = Math.max(...authors.map((b) => b.matchScore));
      const usefulVariation = varied.filter((b) => b.matchScore >= best - 12);
      const pool = usefulVariation.length ? usefulVariation : authors;
      const utility = (b) =>
        b.matchScore -
        8 * Math.max(...result.map((r) => this.similarity(b, r))) +
        1.5 * this.noise(b.id, options.seed ?? 0);
      pool.sort((a, b) => utility(b) - utility(a) || a.id.localeCompare(b.id));
      const chosen = pool[0];
      result.push(chosen);
      remaining.splice(remaining.indexOf(chosen), 1);
    }
    return result;
  },
};
