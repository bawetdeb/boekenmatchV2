const test = require("node:test"),
  assert = require("node:assert/strict"),
  vm = require("node:vm"),
  fs = require("node:fs");
function setup(responses, validImages) {
  const fetched = [],
    loaded = [],
    storage = {};
  const ctx = {
    window: null,
    Map,
    AbortSignal,
    setTimeout,
    clearTimeout,
    localStorage: {
      getItem: (k) => storage[k] || null,
      setItem: (k, v) => (storage[k] = v),
    },
    Image: class {
      set src(v) {
        loaded.push(v);
        this.naturalWidth = validImages.includes(v) ? 120 : 0;
        queueMicrotask(() =>
          this.naturalWidth ? this.onload() : this.onerror(),
        );
      }
    },
    fetch: async (url) => {
      fetched.push(url);
      return { ok: true, json: async () => responses.shift() || {} };
    },
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync("js/coverService.js", "utf8"), ctx);
  return { ...ctx, fetched, loaded, storage };
}
const b = {
  title: "Boy 7",
  author: "Mirjam Mous",
  isbn: "test-isbn",
  coverUrl: "https://example.test/explicit.jpg",
};
test("explicit cover takes precedence and cache contains title-author key", async () => {
  const c = setup([], [b.coverUrl]);
  assert.equal(await c.coverService.findCover(b), b.coverUrl);
  assert.equal(c.fetched.length, 0);
  assert.ok(
    JSON.parse(c.storage["boekenmatch-covers"])[
      b.title + "|" + b.author + "|" + b.isbn
    ],
  );
});
test("ISBN succeeds before metadata search", async () => {
  const url =
    "https://covers.openlibrary.org/b/isbn/test-isbn-M.jpg?default=false";
  const c = setup([], [url]);
  assert.equal(await c.coverService.findCover(b), url);
  assert.equal(c.fetched.length, 0);
});
test("reject mismatching title-author and use verified Google fallback", async () => {
  const url = "https://example.test/google.jpg";
  const c = setup(
    [
      { docs: [{ title: "Other", author_name: ["Mirjam Mous"], cover_i: 12 }] },
      {
        items: [
          {
            volumeInfo: {
              title: b.title,
              authors: [b.author],
              industryIdentifiers: [{ identifier: b.isbn }],
              imageLinks: { thumbnail: url },
            },
          },
        ],
      },
    ],
    [url],
  );
  assert.equal(await c.coverService.findCover(b), url);
  assert.equal(c.fetched.length, 2);
  assert.ok(!c.loaded.some((x) => x.includes("/id/12")));
});
test("broken Open Library image proceeds to Google, then local fallback", async () => {
  const c = setup(
    [
      {
        docs: [
          {
            title: b.title,
            author_name: [b.author],
            isbn: [b.isbn],
            cover_i: 12,
          },
        ],
      },
      { items: [] },
    ],
    [],
  );
  const url = await c.coverService.findCover(b);
  assert.ok(url.startsWith("data:image/svg+xml"));
  assert.equal(c.fetched.length, 2);
  await c.coverService.findCover(b);
  assert.equal(c.fetched.length, 2);
});

test("reject title-author matches belonging to a different ISBN edition", async () => {
  const c = setup(
    [
      {
        docs: [
          {
            title: b.title,
            author_name: [b.author],
            isbn: ["other-isbn"],
            cover_i: 42,
          },
        ],
      },
      {
        items: [
          {
            volumeInfo: {
              title: b.title,
              authors: [b.author],
              industryIdentifiers: [{ identifier: "other-isbn" }],
              imageLinks: { thumbnail: "https://example.test/wrong.jpg" },
            },
          },
        ],
      },
    ],
    ["https://example.test/wrong.jpg"],
  );
  assert.ok(
    (await c.coverService.findCover(b)).startsWith("data:image/svg+xml"),
  );
  assert.ok(!c.loaded.includes("https://example.test/wrong.jpg"));
});
test("cache distinguishes two editions of the same title and author", async () => {
  const c = setup([], [b.coverUrl]);
  await c.coverService.findCover(b);
  await c.coverService.findCover({ ...b, isbn: "second-edition" });
  assert.equal(
    Object.keys(JSON.parse(c.storage["boekenmatch-covers"])).length,
    2,
  );
});
