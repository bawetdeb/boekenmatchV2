"""Read-only import of confirmed matches from Bogerman's public Aura catalogue.
No login, lending actions or personal data. Standard-library dependencies only.
"""
import concurrent.futures, datetime, http.cookiejar, json, re, subprocess, threading, unicodedata, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs
BASE='https://bogerman.auralibrary.nl/'
ROOT=Path(__file__).resolve().parents[1]
class Node:
 def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 def text(self):return ' '.join((c.text() if isinstance(c,Node) else c) for c in self.children).strip()
 def all(self):
  yield self
  for c in self.children:
   if isinstance(c,Node):yield from c.all()
 def klass(self,k):return k in self.attrs.get('class','').split()
class DOM(HTMLParser):
 def __init__(self,html):super().__init__();self.root=Node();self.stack=[self.root];self.feed(html)
 def handle_starttag(self,t,a):
  n=Node(t,a);self.stack[-1].children.append(n)
  if t not in ['img','input','br','hr','meta','link','area','source','wbr']:self.stack.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];break
 def handle_data(self,d):
  if self.stack[-1].tag not in ['script','style']:self.stack[-1].children.append(d)
def normal(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def author(s):
 # Aura appends translator credits after a semicolon.
 s=s.split(';',1)[0].strip()
 if ',' in s:
  last,first=s.split(',',1);s=first+' '+last
 return normal(s)
def same_title(actual,expected):
 # Only this edition label is interchangeable; sequel subtitles remain distinct.
 actual=re.sub(r'\s*;\s*filmeditie\s*$', '', actual, flags=re.I)
 return normal(actual)==normal(expected)
local=threading.local()
def fetch(path):
 if not hasattr(local,'op'):
  local.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  with local.op.open(BASE+'auraicx.aspx',timeout=30) as r:r.read()
 with local.op.open(urljoin(BASE,path),timeout=30) as r:return DOM(r.read().decode('utf-8-sig')).root

def lookup(book):
 root=fetch('auraiczoekenx.aspx?'+urlencode({'field':'title','zoekterm':book['title']}))
 candidates=[]
 for row in root.all():
  if not row.attrs.get('id','').startswith('CPH1_grid_DXDataRow'):continue
  link=next((x for x in row.all() if 'HLTIT' in x.attrs.get('id','')),None)
  who=next((x for x in row.all() if x.klass('author')),None)
  values=[x.text() for x in row.all() if x.klass('value')]
  if link and who and same_title(link.text(),book['title']) and author(who.text())==author(book['author']) and 'Boek' in values:
   candidates.append(link.attrs['href'])
 records=[]
 for path in candidates[:3]:
  doc=fetch(path);title=next((x.text() for x in doc.all() if x.klass('titel')),'');who=next((x.text() for x in doc.all() if x.klass('dtaut')),'')
  if not same_title(title,book['title']) or author(who)!=author(book['author']):continue
  fields={}
  for row in doc.all():
   if row.tag=='tr':
    key=next((x.text() for x in row.all() if x.klass('ajdgeg2')),None)
    value=next((x.text() for x in row.all() if x.klass('ajdgeg3')),None)
    if key:fields[key]=value
  language=(fields.get('Taal') or '').strip()
  if language and language!='Nederlands':continue
  copies=[]
  for row in doc.all():
   if row.tag!='tr':continue
   places=[x.text() for x in row.all() if x.klass('ta1')]
   status=next((x.text() for x in row.all() if x.klass('ta3')),None)
   if places and status:copies.append({'branch':places[0],'location':places[1] if len(places)>1 else '', 'status':status})
  cover=next((x.attrs.get('src','') for x in doc.all() if x.attrs.get('id')=='CPH1_imgCover'),'')
  isbn_match=re.search(r'/(\d{13})\.jpg',cover)
  record_id=parse_qs(urlsplit(path).query).get('DOCSTART',[''])[0]
  if not record_id or not copies:continue
  # Verify deep links without an existing search session; older records may
  # otherwise silently open a different title.
  direct=BASE+'ajdetailsx.aspx?AW='+record_id
  with urllib.request.urlopen(direct,timeout=30) as response:
   landing=DOM(response.read().decode('utf-8-sig')).root
  direct_title=next((x.text() for x in landing.all() if x.klass('titel')),'')
  direct_author=next((x.text() for x in landing.all() if x.klass('dtaut')),'')
  if not same_title(direct_title,book['title']) or author(direct_author)!=author(book['author']):direct=''
  records.append({'id':book['id'],'title':title,'author':who,'isbn':isbn_match.group(1) if isbn_match else '', 'auraId':record_id,'auraUrl':direct,'coverUrl':urljoin(BASE,cover) if cover and 'nietgevonden' not in cover else '', 'copies':copies,'available':any(c['status'].strip().lower()=='aanwezig' for c in copies),'location':'; '.join(c['branch']+' · '+c['location'] for c in copies),'language':'nl' if language=='Nederlands' else '','catalogLevel':fields.get('Niveau','')})
 return next((r for r in records if r['available']),records[0] if records else None)

def main():
 books=json.loads(subprocess.check_output(['node','-e',"global.window=global;require('./data/books.js');process.stdout.write(JSON.stringify(BOOKS))"],cwd=ROOT,text=True))
 found=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  jobs={pool.submit(lookup,b):b for b in books}
  for i,f in enumerate(concurrent.futures.as_completed(jobs),1):
   book=jobs[f]
   try:
    record=f.result()
    if record:found.append(record)
   except Exception as e:errors.append({'title':book['title'],'error':str(e)})
   if i%10==0:print(f'{i}/{len(books)} gecontroleerd; {len(found)} bevestigd; {len(errors)} fouten',flush=True)
 if errors:raise RuntimeError('Import niet opgeslagen wegens onvolledige controle: '+json.dumps(errors,ensure_ascii=False))
 if not found:raise RuntimeError('Geen bevestigde records; bestaande snapshot behouden.')
 snapshot={'source':'aura','catalogUrl':BASE+'auraicx.aspx','checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidateCount':len(books),'records':sorted(found,key=lambda r:r['id'])}
 out=ROOT/'data/aura-catalog.js';temporary=out.with_suffix('.tmp');temporary.write_text('// Public catalogue snapshot; no personal data. Refresh using python scripts/sync_aura.py\nwindow.AURA_CATALOG = '+json.dumps(snapshot,ensure_ascii=False,indent=2)+';\n');temporary.replace(out)
 print(f'Snapshot opgeslagen: {len(found)} bevestigde titels, {sum(r["available"] for r in found)} aanwezig bij controle.',flush=True)
if __name__=='__main__':main()
