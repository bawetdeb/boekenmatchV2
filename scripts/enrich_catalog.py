"""Read-only, resumable work-level enrichment. Never assert an Excel edition.

Public descriptions are evidence, not instructions. No login or lending actions.
Raw responses stay outside the published checkout; only short attributed excerpts
and assessments with evidence are published. TLS validation remains enabled.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from sync_aura import DOM, BASE, author

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path('/workspace/boekenmatch-enrichment-cache')
LOCAL = threading.local()
OPENLIBRARY_LOCK = threading.Lock()
OPENLIBRARY_LAST_REQUEST = 0
REFRESH = False
RULE_VERSION = 'evidence-tags-v5'

# Presence tags only: a mention does not establish an intensity or its absence.
INTEREST_RULES = {
    'voetbal': r'voetbal\w*', 'Formule 1': r'formule\s*1|formule\s*een',
    'fitness': r'fitness|bodybuild\w*', 'vechtsport': r'judo|karate|bokser\w*|boksen|kickboks\w*',
    'basketbal': r'basketbal\w*', 'skateboarden': r'skateboard\w*',
    'wintersport': r'wintersport|snowboard\w*|skiën|skiër\w*',
    'andere sport': r'sport\w*|atletiek|zwemwedstrijd\w*|wielren\w*',
    'games': r'computerspel\w*|videogame\w*|gamer\w*|gamen|onlinegame\w*|gamewereld|game',
    'social media': r'sociale media|social media|instagram|tiktok|facebook',
    'YouTube': r'youtub\w*', 'films': r'filmregisseur\w*|filmwereld|filmster\w*|filmindustrie',
    'muziek': r'muziek\w*|rapper\w*|rapmuziek|rockband\w*|pianist\w*|pianospel|zanger\w*|zangeres\w*',
    'influencers': r'influencer\w*|vlogger\w*', 'reality-tv': r'reality\W*tv|realityshow\w*',
    'computers': r'computer\w*|hacker\w*|hacken|programmeren',
    'AI': r'kunstmatige intelligentie|artificiële intelligentie',
    "auto's": r'autocoureur\w*|autorace\w*|autowereld',
    'motoren': r'motorfiets\w*|motorrace\w*|motorrijder\w*',
    'machines': r'machine\w*|robot\w*', 'bouwen': r'architect\w*|bouwkunde',
    'wetenschap': r'wetenschap\w*|uitvinder\w*|laboratorium',
    'vriendschap': r'vriendschap\w*|beste vriend\w*|boezemvriend\w*',
    'verliefdheid': r'verliefd\w*|smoorverliefd\w*|liefdesverhaal\w*|liefdesrelatie\w*|liefdesperikel\w*|romantiek|romantisch\w*|liefde(?!\s+voor)',
    'relaties': r'relatieproblemen|liefdesrelatie\w*|verkering|verkeren met',
    'familie': r'familie\w*|gezinsproblemen|echtscheiding|gescheiden ouders',
    'school': r'school\w*|klasgenoot\w*|middelbare school|brugklas',
    'pesten': r'pesten|gepest\w*|pesterijen|pestkop\w*',
    'identiteit': r'identiteit\w*|zelfbeeld|zoektocht naar zichzelf',
    'volwassen worden': r'volwassen worden|opgroeien|puberteit',
    'oorlog': r'oorlog\w*|wereldoorlog\w*|burgeroorlog\w*|kernoorlog\w*|nazi\w*|holocaust|concentratiekamp\w*|verzetsstrijd\w*',
    'geschiedenis': r'historische roman|historisch verhaal|in de middeleeuwen|in de negentiende eeuw|in de achttiende eeuw|in de zeventiende eeuw|tweede wereldoorlog|eerste wereldoorlog',
    'criminaliteit': r'criminaliteit|crimine\w*|misdaad\w*|moord\w*|ontvoer\w*|ontvoering\w*|detective\w*',
    'waargebeurde verhalen': r'waargebeurd\w*|autobiografi\w*|biografi\w*|op ware gebeurtenissen',
    'rampen': r'natuurramp\w*|aardbeving\w*|overstroming\w*|tsunami\w*|watersnood\w*',
    'reizen': r'reisverhaal\w*|wereldreis\w*|ontdekkingsreis\w*|avontuurlijke reis|op reis|roadtrip|liftend',
    'magie': r'magie|magisch\w*|tovenaar\w*|tovenares\w*|toverwereld',
    'fantasy': r'fantasy|fantasiewereld|magische wereld|elfen|draken|demon\w*|vampier\w*|fae',
    'monsters': r'monster\w*', 'superkrachten': r'superkracht\w*|superheld\w*',
    'sciencefiction': r'sciencefiction|science fiction|ruimtevaart|ruimteschip\w*|buitenaards\w*',
    'dystopie': r'dystopi\w*|totalitaire samenleving|postapocalyptisch\w*',
    'zombies': r'zombie\w*', 'mythologie': r'mythologi\w*|griekse goden|noorse goden',
    'dieren': r'dieren\w*|dierenarts\w*|dierentuin\w*',
    'natuur': r'natuur\w*|milieu\w*|klimaat\w*', 'paarden': r'paard\w*|pony\w*|manege',
    'honden': r'hond(?:en|je|jes)?|puppy\w*', 'survival': r'survival|overleven in|overleven op|overlevingstocht',
    'politiek': r'politiek\w*|dictatuur\w*|dictator\w*|rebellen|rebellie|revolutie',
}
STORY_RULES = {
    'spanning': r'thriller\w*|spannend\w*|spanning', 'humor': r'humor\w*|humoristisch\w*|komisch\w*|grappig\w*',
    'romantiek': INTEREST_RULES['verliefdheid'], 'mysterie': r'mysterie\w*|raadsel\w*|detective\w*|op onderzoek|verdwijnt|verdwijning\w*',
    'fantasy': INTEREST_RULES['fantasy'], 'oorlog': INTEREST_RULES['oorlog'],
    'school': INTEREST_RULES['school'], 'vriendschap': INTEREST_RULES['vriendschap'],
    'sport': r'sport\w*|voetbal\w*|basketbal\w*',
    'technologie': INTEREST_RULES['computers'] + '|' + INTEREST_RULES['AI'],
    'sciencefiction': INTEREST_RULES['sciencefiction'], 'waargebeurd': INTEREST_RULES['waargebeurde verhalen'],
    'horror': r'horror|griezel\w*', 'psychologie': r'psychologisch\w*|psychologie',
    'feelgood': r'feelgood|feel-good', 'actie': r'actievol\w*|achtervolging\w*',
    'misdaad': INTEREST_RULES['criminaliteit'],
    'emotioneel': r'rouwverwerking|rouw|verdriet|ontroerend\w*|emotionele',
}

# Open Library often supplies English descriptions/subjects for translated works.
for label, pattern in {
    'voetbal': r'soccer|association football', 'games': r'video games?|computer games?|gamers?',
    'vriendschap': r'friendship|best friends?', 'verliefdheid': r'falling in love|love stories|romance',
    'school': r'boarding schools?|school stories|school life', 'familie': r'family life|family relationships',
    'oorlog': r'world war|war stories|holocaust', 'geschiedenis': r'historical fiction|historical novel',
    'criminaliteit': r'crime|detective stories|murder', 'paarden': r'horses|ponies',
    'honden': r'dogs|puppies', 'magie': r'magic|wizards|witchcraft',
    'sciencefiction': r'science fiction|spaceships|space travel|extraterrestrials',
    'dystopie': r'dystopian|dystopias', 'dieren': r'animals', 'muziek': r'music|musicians',
}.items():
    INTEREST_RULES[label] += '|' + pattern
for story, interest in [('romantiek', 'verliefdheid'), ('oorlog', 'oorlog'),
                        ('school', 'school'), ('vriendschap', 'vriendschap'),
                        ('sciencefiction', 'sciencefiction'), ('misdaad', 'criminaliteit')]:
    STORY_RULES[story] = INTEREST_RULES[interest]
STORY_RULES['mysterie'] += r'|mystery|mysteries'
STORY_RULES['humor'] += r'|humorous stories|humorous fiction'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def plot_text(description):
    # Remove leading bibliographic notes, retaining only source text verbatim.
    text = re.sub(r'^(?:Vertaling|Vert\.)\s*van:.*?\b\d{4}\.\s*', '', description, flags=re.I)
    return re.sub(r'^-?\s*Op titelpagina:.*?\.\s*', '', text, flags=re.I)


def normal(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())


def same_title(left, right):
    # Punctuation, spacing and a leading Dutch definite article are harmless.
    # Do not discard subtitles, numbers, edition labels or arbitrary words.
    strip = lambda s: re.sub(r'^(de|het|een)\s+', '', s.strip(), flags=re.I)
    return normal(strip(left)) == normal(strip(right))


def terms(text, rules, source_url):
    found = []
    for label, pattern in rules.items():
        match = re.search(r'(?<!\w)(?:' + pattern + r')(?!\w)', text, flags=re.I)
        if not match:
            continue
        # A negated mention is not positive content evidence.
        prefix = text[max(0, match.start() - 35):match.start()].lower()
        if re.search(r'\b(geen|zonder|niet)\b[^.!?;]{0,25}$', prefix):
            continue
        found.append({'value': label, 'confidence': 'medium', 'kind': 'inference',
                      'method': RULE_VERSION, 'sourceUrl': source_url,
                      'evidence': text[max(0, match.start() - 45):min(len(text), match.end() + 65)]})
    return found


def assess(description, subjects, url):
    # Only descriptions/subject fields, never a title alone, drive classification.
    sentences = re.split(r'(?<=[.!?])\s+', plot_text(description))
    plot = ' '.join(s for s in sentences if not re.search(
        r'\b(auteur|schrijver|schrijfster|(?:jeugd)?roman van rapper|omslag|vertaling van|verfilming|verfilmd|fans van|eerder verscheen|vervolg op)\b', s, re.I))
    text = clean(subjects + '. ' + plot)
    interests = terms(text, INTEREST_RULES, url)
    stories = terms(text, STORY_RULES, url)
    # This catalogue uses "Science fiction" as a broad shelf category, also
    # for fantasy. Do not classify supernatural fantasy as SF on that alone.
    science_evidence = terms(plot, {'sciencefiction': INTEREST_RULES['sciencefiction']}, url)
    if not science_evidence:
        interests = [r for r in interests if r['value'] != 'sciencefiction']
        stories = [r for r in stories if r['value'] != 'sciencefiction']
    fantasy_evidence = terms(plot, {'fantasy': INTEREST_RULES['fantasy']}, url)
    if not fantasy_evidence:
        interests = [r for r in interests if r['value'] != 'fantasy']
        stories = [r for r in stories if r['value'] != 'fantasy']
    school_mentions = re.findall(r'\bschool\w*\b', plot, re.I)
    if len(school_mentions) == 1 and re.search(r'laatste schooldag', plot, re.I) and not re.search(r'school', subjects, re.I):
        interests = [r for r in interests if r['value'] != 'school']
        stories = [r for r in stories if r['value'] != 'school']
    notes = []
    if re.search(r'science fiction', subjects, re.I) and not science_evidence:
        notes.append('Brede cataloguscategorie Science fiction niet als specifiek SF-genre overgenomen zonder steun in de beschrijving.')
    if re.search(r'fantasy', subjects, re.I) and not fantasy_evidence:
        notes.append('Cataloguscategorie Fantasy niet als specifiek fantasygenre overgenomen zonder steun in de beschrijving.')
    return {'interests': interests,
            'storyTags': stories,
            'themeIntensities': None, 'readingDifficulty': None,
            'schoolLevels': None, 'sensitiveTopicsComplete': False,
            'notes': notes,
            'explanation': 'Automatische inschatting op basis van expliciete termen in de bronbeschrijving; geen inhoudslezing of intensiteitsmeting.'}


def request(url):
    global OPENLIBRARY_LAST_REQUEST
    if urllib.parse.urlsplit(url).hostname == 'openlibrary.org':
        with OPENLIBRARY_LOCK:
            time.sleep(max(0, 1.1 - (time.monotonic() - OPENLIBRARY_LAST_REQUEST)))
            OPENLIBRARY_LAST_REQUEST = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent': 'BoekenMatchV2/1.0 (educational, read-only catalog enrichment)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def aura_fetch(path):
    # Existing cookie/session machinery isolates each worker and preserves proxies.
    from sync_aura import fetch
    return fetch(path)


def lookup_aura(book):
    search_url = BASE + 'auraiczoekenx.aspx?' + urllib.parse.urlencode({'field': 'title', 'zoekterm': book['title']})
    result = aura_fetch(search_url)
    candidates = []
    for row in result.all():
        if not row.attrs.get('id', '').startswith('CPH1_grid_DXDataRow'):
            continue
        link = next((x for x in row.all() if 'HLTIT' in x.attrs.get('id', '')), None)
        who = next((x for x in row.all() if x.klass('author')), None)
        values = [x.text() for x in row.all() if x.klass('value')]
        if link and who and same_title(link.text(), book['title']) and author(who.text()) == author(book['author']) and 'Boek' in values:
            candidates.append(link.attrs['href'])
    if not candidates:
        return None
    documents = []
    for path in dict.fromkeys(candidates[:3]):
        doc = aura_fetch(path)
        title = next((x.text() for x in doc.all() if x.klass('titel')), '')
        who = next((x.text() for x in doc.all() if x.klass('dtaut')), '')
        if not same_title(title, book['title']) or author(who) != author(book['author']):
            continue
        fields = {}
        for row in doc.all():
            if row.tag == 'tr':
                key = next((x.text() for x in row.all() if x.klass('ajdgeg2')), None)
                value = next((x.text() for x in row.all() if x.klass('ajdgeg3')), None)
                if key:
                    fields[clean(key)] = clean(value)
        description = clean(next((x.text() for x in doc.all() if x.klass('dtabs')), ''))
        # Record a search URL that works without a session. Never claim a stable
        # Aura ID/deep link just because a session-scoped DOCSTART matched.
        documents.append({'provider': 'Bogerman Aura', 'url': search_url,
                          'checkedAt': now(), 'matchedTitle': clean(title), 'matchedAuthor': clean(who),
                          'identityConfidence': 'high', 'identityScope': 'work',
                          'editionVerified': False, 'description': description,
                          'subjects': fields.get('Thema', ''), 'fields': fields})
    if not documents:
        return None
    # Select the richest description, retaining variant evidence for conflicts.
    documents.sort(key=lambda d: len(d['description']), reverse=True)
    selected = documents[0]
    selected['conflicts'] = []
    languages = {d['fields'].get('Taal') for d in documents if d['fields'].get('Taal')}
    if len(languages) > 1:
        selected['conflicts'].append({'field': 'language', 'values': sorted(languages)})
    return selected


def lookup_openlibrary(book):
    url = 'https://openlibrary.org/search.json?' + urllib.parse.urlencode({
        'title': book['title'], 'author': book['author'].split(';')[0], 'limit': 5,
        'fields': 'key,title,author_name,language,subject'})
    data = json.loads(request(url))
    matches = [d for d in data.get('docs', []) if same_title(d.get('title', ''), book['title']) and
               any(author(a) == author(book['author']) for a in d.get('author_name', []))]
    if len(matches) != 1:
        return None
    match = matches[0]
    work_url = 'https://openlibrary.org' + match['key']
    work = json.loads(request(work_url + '.json'))
    description = work.get('description', '')
    if isinstance(description, dict):
        description = description.get('value', '')
    return {'provider': 'Open Library', 'url': work_url, 'checkedAt': now(),
            'matchedTitle': match['title'], 'matchedAuthor': book['author'],
            'identityConfidence': 'high', 'identityScope': 'work', 'editionVerified': False,
            'description': clean(description), 'subjects': '; '.join(work.get('subjects', [])),
            'fields': {}, 'conflicts': []}


def publish(book, evidence, attempts):
    result = {'id': book['id'], 'attempts': attempts, 'status': 'unresolved',
              'facts': {}, 'assessments': None, 'sources': [], 'conflicts': [],
              'recommendationReady': False, 'editionVerified': False,
              'missingFields': ['isbn', 'pages', 'coverUrl', 'language', 'summary',
                                'readingDifficulty', 'schoolLevels', 'available', 'auraId']}
    if not evidence:
        return result
    source = {k: v for k, v in evidence.items() if k not in ['description', 'subjects', 'fields', 'conflicts']}
    source['descriptionSha256'] = hashlib.sha256(evidence['description'].encode()).hexdigest()
    result['sources'] = [source]
    result['conflicts'] = evidence.get('conflicts', [])
    excerpt = plot_text(evidence['description'])
    if len(excerpt) > 220:
        excerpt = excerpt[:217].rsplit(' ', 1)[0] + '…'
    for name, value in [('summary', excerpt), ('subjects', evidence['subjects'])]:
        if value:
            result['facts'][name] = {'value': value, 'sourceUrl': source['url'],
                                    'checkedAt': source['checkedAt'], 'confidence': 'high',
                                    'scope': 'work', 'excerpt': name == 'summary'}
    language = evidence['fields'].get('Taal')
    codes = {'Nederlands': 'nl', 'Engels': 'en', 'Duits': 'de', 'Frans': 'fr'}
    if language in codes and not any(c['field'] == 'language' for c in result['conflicts']):
        result['facts']['language'] = {'value': codes[language], 'sourceUrl': source['url'],
                                       'checkedAt': source['checkedAt'], 'confidence': 'high', 'scope': 'catalog-record'}
    result['assessments'] = assess(evidence['description'], evidence['subjects'], source['url'])
    for item in result['assessments']['interests'] + result['assessments']['storyTags']:
        item['checkedAt'] = source['checkedAt']
    result['recommendationReady'] = bool(len(plot_text(evidence['description'])) >= 80 and
                                         (result['assessments']['interests'] or result['assessments']['storyTags']))
    result['status'] = 'partial' if result['facts'] or result['assessments']['interests'] or result['assessments']['storyTags'] else 'unresolved'
    result['missingFields'] = [f for f in result['missingFields'] if f not in result['facts']]
    return result


def collect(book, fallback=False):
    cache = CACHE / (book['id'] + '.json')
    previous = json.loads(cache.read_text()) if cache.exists() else None
    if previous and not REFRESH and (previous.get('evidence') or not fallback or previous.get('fallbackAttempted')):
        return publish(book, previous.get('evidence'), previous['attempts'])
    attempts = previous['attempts'] if previous else []
    evidence = None
    if previous and not REFRESH and fallback and any(a.get('error', '').startswith('HTTP Error 500') for a in attempts):
        # One delayed retry for a confirmed transient server error, at the
        # fallback stage's lower concurrency, preserving the original failure.
        try:
            evidence = lookup_aura(book)
            attempts.append({'provider': 'Bogerman Aura', 'checkedAt': now(), 'outcome': 'matched-on-delayed-retry' if evidence else 'no-confirmed-match-on-delayed-retry'})
        except Exception as exc:
            attempts.append({'provider': 'Bogerman Aura', 'checkedAt': now(), 'outcome': 'retry-error', 'error': str(exc)[:240]})
    if not previous or REFRESH:
        try:
            evidence = lookup_aura(book)
            attempts.append({'provider': 'Bogerman Aura', 'checkedAt': now(), 'outcome': 'matched' if evidence else 'no-confirmed-match'})
        except Exception as exc:
            attempts.append({'provider': 'Bogerman Aura', 'checkedAt': now(), 'outcome': 'error', 'error': str(exc)[:240]})
    if fallback and not evidence:
        try:
            evidence = lookup_openlibrary(book)
            attempts.append({'provider': 'Open Library', 'checkedAt': now(), 'outcome': 'matched' if evidence else 'no-confirmed-match'})
        except Exception as exc:
            attempts.append({'provider': 'Open Library', 'checkedAt': now(), 'outcome': 'error', 'error': str(exc)[:240]})
        time.sleep(1)  # Anonymous Open Library limit: at most one request/second.
    if not evidence and REFRESH and previous and previous.get('evidence'):
        evidence = previous['evidence']
        attempts.append({'provider': 'pipeline', 'checkedAt': now(), 'outcome': 'retained-previous-evidence-after-refresh-failure'})
    payload = {'evidence': evidence, 'attempts': attempts, 'fallbackAttempted': fallback}
    temporary = cache.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False))
    temporary.replace(cache)
    return publish(book, evidence, attempts)


def main():
    global REFRESH
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--batch-size', type=int, default=50)
    parser.add_argument('--fallback', action='store_true')
    parser.add_argument('--refresh', action='store_true', help='Explicitly recheck the public sources; retain old dated evidence on failure')
    args = parser.parse_args()
    REFRESH = args.refresh
    CACHE.mkdir(parents=True, exist_ok=True)
    source = json.loads((ROOT / 'data/library-catalog.json').read_text())
    actual_hash = hashlib.sha256((ROOT / 'data/sources/jeugdboeken.xlsx').read_bytes()).hexdigest()
    if actual_hash != source['sourceSha256']:
        raise ValueError('Excel source changed: reimport and review before enrichment')
    if args.start % args.batch_size or (args.limit and args.limit % args.batch_size and args.start + args.limit < source['recordCount']):
        raise ValueError('Use aligned whole batches to preserve existing checkpoints')
    books = source['records'][args.start:args.start + args.limit if args.limit else None]
    output = ROOT / 'data/enrichment'
    output.mkdir(exist_ok=True)
    for offset in range(0, len(books), args.batch_size):
        batch = books[offset:offset + args.batch_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=1 if args.fallback else 3) as pool:
            records = list(pool.map(lambda b: collect(b, args.fallback), batch))
        batch_index = (args.start + offset) // args.batch_size
        path = output / f'batch-{batch_index:04d}.json'
        payload = {'schemaVersion': 1, 'ruleVersion': RULE_VERSION, 'sourceSha256': source['sourceSha256'], 'records': records}
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(path)
        print(f"Batch {batch_index}: {args.start + offset + len(batch)}/{source['recordCount']}; matched {sum(bool(r['sources']) for r in records)}/{len(batch)}; ready {sum(r['recommendationReady'] for r in records)}", flush=True)
    # Rebuild one client snapshot from the checkpointed, disjoint batches.
    all_records = {}
    for path in sorted(output.glob('batch-*.json')):
        data = json.loads(path.read_text())
        if data['sourceSha256'] != source['sourceSha256']:
            raise ValueError('Source workbook changed; do not mix checkpoints')
        if data['ruleVersion'] != RULE_VERSION:
            raise ValueError('Assessment rules changed: rebuild all batches from cache')
        for record in data['records']:
            if record['id'] in all_records:
                raise ValueError('Overlapping batches')
            all_records[record['id']] = record
    snapshot = {'schemaVersion': 1, 'ruleVersion': RULE_VERSION,
                'sourceSha256': source['sourceSha256'], 'checkedAt': now(),
                'recordCount': len(all_records), 'records': list(all_records.values())}
    (ROOT / 'data/enriched-catalog.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    print('Published snapshot', len(all_records), 'records', flush=True)


if __name__ == '__main__':
    main()
