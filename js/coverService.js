window.coverService = {
  fallback(book) {
    const escape = (s) => String(s).replace(/[<>&"']/g, "");
    const title = escape(book.title),
      author = escape(book.author);
    return (
      "data:image/svg+xml;charset=utf-8," +
      encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="460"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#612c8d"/><stop offset="1" stop-color="#d9233f"/></linearGradient></defs><rect width="320" height="460" rx="12" fill="url(#g)"/><circle cx="270" cy="70" r="90" fill="#f4c84a" opacity=".35"/><text x="25" y="200" fill="white" font-size="23" font-family="sans-serif"><tspan x="25">${title.slice(0, 23)}</tspan><tspan x="25" dy="30">${title.slice(23, 46)}</tspan></text><text x="25" y="365" fill="white" font-size="17" font-family="sans-serif">${author}</text><text x="25" y="420" fill="#f4c84a" font-size="14">BOEKENMATCH · TESTCOLLECTIE</text></svg>`,
      )
    );
  },
  memory: new Map(),
  async findCover(book) {
    const key = book.title + "|" + book.author + "|" + (book.isbn || "");
    if (this.memory.has(key)) return this.memory.get(key);
    const operation = this.resolve(book, key);
    this.memory.set(key, operation);
    return operation;
  },
  async resolve(book, key) {
    let cache = {};
    try {
      cache = JSON.parse(localStorage.getItem("boekenmatch-covers") || "{}");
    } catch {}
    const load = (url) =>
      new Promise((resolve) => {
        if (!url) return resolve(false);
        const img = new Image();
        const timer = setTimeout(() => resolve(false), 2500);
        img.onload = () => {
          clearTimeout(timer);
          resolve(img.naturalWidth > 1);
        };
        img.onerror = () => {
          clearTimeout(timer);
          resolve(false);
        };
        img.src = url;
      });
    const save = (url) => {
      try {
        const latest = JSON.parse(
          localStorage.getItem("boekenmatch-covers") || "{}",
        );
        latest[key] = url;
        localStorage.setItem("boekenmatch-covers", JSON.stringify(latest));
      } catch {}
      return url;
    };
    if (book.coverUrl && (await load(book.coverUrl)))
      return save(book.coverUrl);
    if (cache[key] && (await load(cache[key]))) return cache[key];
    if (book.isbn) {
      const url =
        "https://covers.openlibrary.org/b/isbn/" +
        encodeURIComponent(book.isbn) +
        "-M.jpg?default=false";
      if (await load(url)) return save(url);
    }
    const normal = (s) =>
      String(s)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]/g, "");
    const valid = (title, authors, isbns = []) =>
      normal(title) === normal(book.title) &&
      authors.some((a) => normal(a) === normal(book.author)) &&
      (!book.isbn || isbns.some((isbn) => normal(isbn) === normal(book.isbn)));
    try {
      const r = await fetch(
        "https://openlibrary.org/search.json?title=" +
          encodeURIComponent(book.title) +
          "&author=" +
          encodeURIComponent(book.author) +
          "&limit=3",
        { signal: AbortSignal.timeout(2500) },
      );
      if (r.ok) {
        const d = await r.json();
        const match = d.docs?.find(
          (x) => x.cover_i && valid(x.title, x.author_name || [], x.isbn || []),
        );
        if (match) {
          const url =
            "https://covers.openlibrary.org/b/id/" +
            match.cover_i +
            "-M.jpg?default=false";
          if (await load(url)) return save(url);
        }
      }
    } catch {}
    try {
      const r = await fetch(
        "https://www.googleapis.com/books/v1/volumes?q=" +
          encodeURIComponent(
            "intitle:" + book.title + " inauthor:" + book.author,
          ) +
          "&maxResults=3",
        { signal: AbortSignal.timeout(2500) },
      );
      if (r.ok) {
        const d = await r.json();
        const match = d.items?.find((x) =>
          valid(
            x.volumeInfo?.title,
            x.volumeInfo?.authors || [],
            (x.volumeInfo?.industryIdentifiers || []).map((i) => i.identifier),
          ),
        );
        if (match?.volumeInfo.imageLinks?.thumbnail) {
          const url = match.volumeInfo.imageLinks.thumbnail.replace(
            /^http:/,
            "https:",
          );
          if (await load(url)) return save(url);
        }
      }
    } catch {}
    return this.fallback(book);
  },
};
