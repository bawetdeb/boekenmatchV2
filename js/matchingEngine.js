window.MATCH_WEIGHTS = {
  level: 0.25,
  interests: 0.25,
  themes: 0.25,
  readingStyle: 0.1,
  length: 0.05,
  mood: 0.1,
};
window.matchingEngine = {
  clamp(n, min = 0, max = 1) {
    return Math.max(min, Math.min(max, n));
  },
  eligible(b, p, options = {}) {
    const levels = ["basis", "kader", "gt"],
      target = levels.indexOf(p.level);
    return (
      b.available !== false &&
      target >= 0 &&
      b.levels.some(
        (l) => levels.includes(l) && Math.abs(levels.indexOf(l) - target) <= 1,
      ) &&
      !(p.avoidTopics || []).some((t) => b.sensitiveTopics.includes(t)) &&
      (!p.language || b.language === p.language) &&
      (!options.requireAura || (b.auraId && b.catalogSource === "aura"))
    );
  },
  interestStrength(b, interest) {
    if (b.interests.includes(interest)) return 1;
    const related = {
      "andere sport": "sport",
      fitness: "sport",
      basketbal: "sport",
      vechtsport: "sport",
      skateboarden: "sport",
      wintersport: "sport",
      "Formule 1": "sport",
      politiek: "geschiedenis",
      "andere landen": "reizen",
      "volwassen worden": "identiteit",
      films: "entertainment",
      series: "entertainment",
      YouTube: "social media",
      influencers: "social media",
      "reality-tv": "entertainment",
    };
    return related[interest] && b.interests.includes(related[interest])
      ? 0.3
      : 0;
  },
  themeValue(b, key) {
    return this.clamp((b.themes[key] ?? 0) / 5);
  },
  evaluate(b, p, feedback = {}) {
    const interests = p.interests || [],
      selected = p.storyPreferences || [],
      intensities = Object.entries(p.themes || {});
    const importance = (i) => (i === p.primaryInterest ? 2 : 1);
    const total = interests.reduce((s, i) => s + importance(i), 0);
    const interest = total
      ? interests.reduce(
          (s, i) => s + importance(i) * this.interestStrength(b, i),
          0,
        ) / total
      : null;
    const ability = p.readingAbility ?? 2,
      capacity = { 1: 2, 2: 3, 3: 5 }[ability] || 3;
    const level =
      (b.levels.includes(p.level) ? 1 : 0.12) * 0.75 +
      0.25 * this.clamp(1 - Math.max(0, b.readingDifficulty - capacity) / 3);
    const wanted = p.readingDifficulty;
    const difficulty =
      wanted == null
        ? null
        : this.clamp(1 - Math.abs(b.readingDifficulty - wanted) / 4);
    const tempo =
      p.readingSpeed == null
        ? null
        : this.clamp(1 - Math.abs(b.readingSpeed - p.readingSpeed) / 4);
    let styleParts = [difficulty, tempo].filter((x) => x !== null);
    if (p.readingMotivation <= 2)
      styleParts.push(
        (this.clamp(1 - (b.chapterLength - 1) / 5) +
          this.themeValue(b, "actie") +
          this.clamp((b.narrativeClarity || 3) / 5) +
          this.clamp((b.fastStart || b.readingSpeed) / 5)) /
          4,
      );
    const style = styleParts.length
      ? styleParts.reduce((s, v) => s + v, 0) / styleParts.length
      : null;
    const story = selected.length
      ? selected.reduce((s, k) => s + this.themeValue(b, k), 0) /
        selected.length
      : null;
    const intensity = intensities.length
      ? intensities.reduce(
          (s, [k, v]) => s + 1 - Math.abs((b.themes[k] || 0) - v) / 5,
          0,
        ) / intensities.length
      : null;
    const realism =
      p.realismFantasy == null
        ? null
        : this.clamp(1 - Math.abs(b.realismFantasy - p.realismFantasy) / 4);
    const moodParts = [intensity, realism].filter((x) => x !== null);
    const parts = {
      level,
      interests: interest,
      themes: story,
      readingStyle: style,
      length:
        p.maxPages == null
          ? null
          : this.clamp(1 - Math.max(0, b.pages - p.maxPages) / 400),
      mood: moodParts.length
        ? moodParts.reduce((s, v) => s + v, 0) / moodParts.length
        : null,
    };
    const active = Object.entries(MATCH_WEIGHTS).filter(
      ([k, w]) => parts[k] !== null && Number.isFinite(w) && w > 0,
    );
    const weightTotal = active.reduce((s, [, w]) => s + w, 0);
    const weighted = active.reduce((s, [k, w]) => s + w * parts[k], 0);
    const combinationPossible =
      total > 0 && (selected.length > 0 || intensities.some(([, v]) => v >= 4));
    const combination = combinationPossible
      ? 0.05 *
        (interest || 0) *
        Math.max(
          0,
          ...selected.map((k) => this.themeValue(b, k)),
          ...intensities
            .filter(([, v]) => v >= 4)
            .map(([k]) => this.themeValue(b, k)),
        )
      : 0;
    let penalty = 0;
    if (p.readingMotivation <= 2)
      penalty +=
        Math.max(0, b.readingDifficulty - 2) * 0.05 +
        Math.max(0, b.pages - 200) / 4000 +
        Math.max(0, 4 - b.readingSpeed) * 0.03;
    if (p.schoolYear && !b.schoolYear.includes(Number(p.schoolYear)))
      penalty += 0.04;
    if (p.realismFantasy === 1 && b.realismFantasy >= 4) penalty += 0.12;
    const maximum = weightTotal + (combinationPossible ? 0.05 : 0);
    const base = maximum
      ? (100 * (weighted + combination - penalty)) / maximum
      : 0;
    let adjustment = 0;
    for (const [id, f] of Object.entries(feedback)) {
      const source = this.books?.find((x) => x.id === id);
      if (source && [1, -1].includes(f))
        adjustment += f * 8 * diversification.similarity(b, source);
    }
    adjustment = this.clamp(adjustment, -15, 15);
    return {
      matchScore: Math.round(this.clamp(base + adjustment, 0, 100)),
      parts,
      weighted,
      combination,
      penalty,
      maximum,
      feedbackAdjustment: adjustment,
    };
  },
  scoreBook(b, p, feedback = {}) {
    return this.evaluate(b, p, feedback).matchScore;
  },
  reasons(b, p) {
    const r = [],
      hit = (p.interests || []).filter((i) => b.interests.includes(i));
    if (hit.length) r.push("Past bij " + hit.slice(0, 2).join(" en "));
    const desired = (p.storyPreferences || []).filter(
      (k) => (b.themes[k] || 0) >= 4,
    );
    if (desired.length) r.push("Veel " + desired.slice(0, 2).join(" en "));
    else {
      const intensity = Object.entries(p.themes || {}).find(
        ([k, v]) => v >= 4 && (b.themes[k] || 0) >= 4,
      );
      if (intensity) r.push("Veel " + intensity[0]);
    }
    if (b.levels.includes(p.level)) r.push("Past bij jouw niveau");
    if (b.readingDifficulty <= 2 && p.readingMotivation <= 2)
      r.push("Toegankelijk te lezen");
    if (b.readingSpeed >= 4 && p.readingSpeed >= 4)
      r.push("Een verhaal met vaart");
    if (p.maxPages != null && b.pages <= p.maxPages)
      r.push("Binnen jouw gewenste boeklengte");
    return r.slice(0, 3);
  },
  recommend(books, p, limit = 5, options = {}) {
    this.books = books;
    const excluded = new Set(options.exclude || []),
      feedback = options.feedback || {};
    const ranked = books
      .filter((b) => this.eligible(b, p, options))
      .map((b) => ({
        ...b,
        matchScore: this.scoreBook(b, p, feedback),
        matchReasons: this.reasons(b, p),
      }))
      .sort((a, b) => b.matchScore - a.matchScore || a.id.localeCompare(b.id));
    let fresh = ranked
      .filter((b) => !excluded.has(b.id) && feedback[b.id] !== -1)
      .map((b) => ({ ...b, noveltyTier: 0 }));
    if (fresh.length < limit) {
      const seen = ranked
        .filter((b) => excluded.has(b.id) && feedback[b.id] !== -1)
        .map((b) => ({ ...b, noveltyTier: 1 }));
      fresh = [...fresh, ...seen];
      if (fresh.length < limit) {
        const rejected = ranked
          .filter((b) => feedback[b.id] === -1)
          .map((b) => ({ ...b, noveltyTier: 2 }));
        fresh = [...fresh, ...rejected];
      }
    }
    return diversification.select(fresh, limit, { seed: options.seed ?? 0 });
  },
};
