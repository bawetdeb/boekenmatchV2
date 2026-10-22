"""Download catalog covers with verified work identity, not invented editions."""
import concurrent.futures
import argparse
import hashlib
import io
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit, parse_qsl, quote

from PIL import Image, ImageStat
from enrich_catalog import ROOT, now, normal, same_title, request
from sync_aura import BASE, author, fetch

CACHE = Path('/workspace/boekenmatch-cover-cache')
ASSETS = ROOT / 'assets/covers'


def work_key(book):
    return normal(re.sub(r'^(de|het|een)\s+', '', book['title'].strip(), flags=re.I)) + '|' + author(book['author'])


def inspect_image(data):
    with Image.open(io.BytesIO(data)) as image:
        image.verify()
    with Image.open(io.BytesIO(data)) as image:
        width, height = image.size
        if image.format not in ['JPEG', 'PNG', 'WEBP'] or width < 70 or height < 100 or not 0.4 < width / height < 1.21:
            raise ValueError('Image is not a usable book-cover format/size')
        if max(ImageStat.Stat(image.convert('RGB')).stddev) < 8:
            raise ValueError('Blank or near-blank placeholder')
        return width, height, {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}[image.format]


def download(url, source, book):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ['bogerman.auralibrary.nl', 'covers.openlibrary.org']:
        raise ValueError('Unsupported cover destination')
    if any(word in parsed.path.lower() for word in ['nietgevonden', 'nocover', 'noimage', 'geenafbeelding']):
        raise ValueError('Catalog placeholder URL')
    url = parsed._replace(path=quote(parsed.path, safe='/%:@')).geturl()
    data = request(url)
    width, height, extension = inspect_image(data)
    digest = hashlib.sha256(data).hexdigest()
    relative = f'assets/covers/{digest}.{extension}'
    destination = ROOT / relative
    if not destination.exists():
        destination.write_bytes(data)
    return {'url': relative, 'sourceImageUrl': url, 'sourceUrl': source,
            'checkedAt': now(), 'sha256': digest, 'width': width, 'height': height,
            'matchedTitle': book['title'], 'matchedAuthor': book['author'],
            'identityConfidence': 'high', 'editionVerified': False,
            'scope': 'school-catalog-cover' if parsed.hostname == 'bogerman.auralibrary.nl' else 'illustrative-work-cover'}


def lookup(book):
    source = BASE + 'auraiczoekenx.aspx?' + urlencode({'field': 'title', 'zoekterm': book['title']})
    search = fetch(source)
    paths = []
    for row in search.all():
        if not row.attrs.get('id', '').startswith('CPH1_grid_DXDataRow'):
            continue
        link = next((x for x in row.all() if 'HLTIT' in x.attrs.get('id', '')), None)
        who = next((x for x in row.all() if x.klass('author')), None)
        values = [x.text() for x in row.all() if x.klass('value')]
        if link and who and same_title(link.text(), book['title']) and author(who.text()) == author(book['author']) and 'Boek' in values:
            paths.append(link.attrs['href'])
    covers = []
    errors = []
    seen = set()
    for path in dict.fromkeys(paths[:3]):
        detail = fetch(path)
        title = next((x.text() for x in detail.all() if x.klass('titel')), '')
        who = next((x.text() for x in detail.all() if x.klass('dtaut')), '')
        if not same_title(title, book['title']) or author(who) != author(book['author']):
            continue
        image = next((x.attrs.get('src') for x in detail.all() if x.attrs.get('id') == 'CPH1_imgCover'), None)
        if not image:
            continue
        url = urljoin(BASE, image)
        parsed = urlsplit(url)
        query = dict(parse_qsl(parsed.query))
        if 'height' in query:
            query['height'] = '360'
            url = parsed._replace(query=urlencode(query)).geturl()
        if url in seen:
            continue
        seen.add(url)
        try:
            cover = download(url, source, {'title': title, 'author': who})
            if not any(c['sha256'] == cover['sha256'] for c in covers):
                covers.append(cover)
        except Exception as exc:
            errors.append(str(exc)[:220])
    return {'covers': covers, 'errors': errors, 'checkedAt': now(), 'sourceUrl': source}


def collect(book):
    key = hashlib.sha256(work_key(book).encode()).hexdigest()
    path = CACHE / (key + '.json')
    if path.exists():
        result = json.loads(path.read_text())
        if all((ROOT / c['url']).exists() for c in result['covers']):
            return result
    try:
        result = lookup(book)
    except Exception as exc:
        result = {'covers': [], 'errors': [str(exc)[:220]], 'checkedAt': now()}
    result['title'] = book['title']
    result['author'] = book['author']
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    temporary.replace(path)
    return result


def openlibrary_fallback(book, result):
    if result['covers'] or result.get('fallbackAttempted'):
        return result
    result['fallbackAttempted'] = True
    if any("ascii" in error or "control characters" in error for error in result['errors']):
        # Retry only the diagnosed URL-encoding failure after applying RFC URL
        # escaping; preserve the original error rather than hiding the attempt.
        try:
            corrected = lookup(book)
            result['covers'] = corrected['covers']
            result['errors'].extend(corrected['errors'])
        except Exception as exc:
            result['errors'].append('URL correction: ' + str(exc)[:220])
        if result['covers']:
            path = CACHE / (hashlib.sha256(work_key(book).encode()).hexdigest() + '.json')
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            return result
    source = 'https://openlibrary.org/search.json?' + urlencode({
        'title': book['title'], 'author': book['author'].split(';')[0], 'limit': 5,
        'fields': 'key,title,author_name,cover_i'})
    try:
        data = json.loads(request(source))
        matches = [r for r in data.get('docs', []) if same_title(r.get('title', ''), book['title']) and
                   any(author(a) == author(book['author']) for a in r.get('author_name', [])) and r.get('cover_i')]
        if len(matches) == 1 and re.fullmatch(r'/works/OL\d+W', matches[0].get('key', '')):
            match = matches[0]
            cover = download(f"https://covers.openlibrary.org/b/id/{int(match['cover_i'])}-L.jpg?default=false",
                             'https://openlibrary.org' + match['key'],
                             {'title': match['title'], 'author': book['author']})
            result['covers'] = [cover]
    except Exception as exc:
        result['errors'].append('Open Library: ' + str(exc)[:220])
    key = hashlib.sha256(work_key(book).encode()).hexdigest()
    path = CACHE / (key + '.json')
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    temporary.replace(path)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fallback', action='store_true', help='Try Open Library for books without school catalog covers')
    args = parser.parse_args()
    CACHE.mkdir(exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    excel = json.loads((ROOT / 'data/library-catalog.json').read_text())
    legacy = json.loads(subprocess.check_output(['node', '-e',
        "global.window=global;require('./data/books.js');require('./data/aura-catalog.js');process.stdout.write(JSON.stringify(AURA_CATALOG.records.map(r=>({id:r.id,title:r.title,author:BOOKS.find(b=>b.id===r.id).author}))))"], cwd=ROOT))
    groups = {}
    for book in excel['records'] + legacy:
        key = work_key(book)
        if key not in groups:
            groups[key] = {'book': book, 'ids': []}
        groups[key]['ids'].append(book['id'])
    records = {}
    review_path = ROOT / 'data/cover-review.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else {'approved': [], 'rejected': []}
    approved = {item['workKey']: item for item in review['approved']}
    approved_images = {item['cover']['sha256']: item['workKey'] for item in review['approved']}
    quarantined = set(review.get('quarantinedImageHashes', []))
    old_manifest = ROOT / 'data/cover-catalog.json'
    rejected_hashes = set()
    if args.fallback and old_manifest.exists():
        old_records = json.loads(old_manifest.read_text()).get('records', {})
        rejected_hashes = {c['sha256'] for record in old_records.values() for c in record.get('rejectedSharedImages', [])}
    items = list(groups.values())
    for offset in range(0, len(items), 50):
        batch = items[offset:offset + 50]
        if args.fallback:
            results = []
            for item in batch:
                result = collect(item['book'])
                result['covers'] = [c for c in result['covers'] if c['sha256'] not in rejected_hashes]
                results.append(openlibrary_fallback(item['book'], result))
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                results = list(pool.map(lambda item: collect(item['book']), batch))
        for item, result in zip(batch, results):
            key = work_key(item['book'])
            rejected = {entry['sha256'] for entry in review['rejected'] if entry['workKey'] == key}
            result['covers'] = [c for c in result['covers'] if c['sha256'] not in rejected]
            if key in approved:
                reviewed = approved[key]
                result['covers'] = [reviewed['cover']] + [c for c in result['covers'] if c['sha256'] != reviewed['cover']['sha256']]
                result['visualReview'] = {'reviewedAt': reviewed['reviewedAt'], 'review': reviewed['review']}
            for book_id in item['ids']:
                records[book_id] = result
        print(f"Covers: {min(offset+50,len(items))}/{len(items)} works; {sum(bool(r['covers']) for r in records.values())}/{len(records)} records with images", flush=True)
    # A shared image for different works usually indicates a generic placeholder
    # or a catalog mistake. Keep such candidates out of the automatic selection.
    owners = defaultdict(set)
    for result in records.values():
        for cover in result['covers']:
            owners[cover['sha256']].add(work_key(result))
    for result in records.values():
        def allowed(cover):
            digest = cover['sha256']
            if digest in approved_images:
                return approved_images[digest] == work_key(result)
            return digest not in quarantined and len(owners[digest]) == 1
        rejected = [c for c in result['covers'] if not allowed(c)]
        if rejected:
            result['rejectedSharedImages'] = rejected
            result['covers'] = [c for c in result['covers'] if allowed(c)]
    snapshot = {'schemaVersion': 1, 'sourceSha256': excel['sourceSha256'], 'complete': True,
                'checkedAt': now(), 'records': records,
                'report': {'excelRows': len(excel['records']), 'searchedWorks': len(items),
                  'excelRowsWithCovers': sum(bool(records[b['id']]['covers']) for b in excel['records']),
                  'recordsWithCovers': sum(bool(r['covers']) for r in records.values()),
                  'recordsWithMultipleCovers': sum(len(r['covers']) > 1 for r in records.values())}}
    temporary = ROOT / 'data/cover-catalog.tmp'
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(ROOT / 'data/cover-catalog.json')
    print(json.dumps(snapshot['report']), flush=True)


if __name__ == '__main__':
    main()
