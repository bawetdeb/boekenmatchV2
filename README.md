# BoekenMatch — Fase 1

Een statische, Nederlandstalige boekenquiz voor vmbo-leerlingen van csg Bogerman. Werkt zonder account, backend, buildstap of npm-dependencies.

## Starten

Gebruik de bestaande projectmap; een extra Git-worktree is niet nodig.

```bash
cd /workspace/boekenmatchV2
python -m http.server 8000
```

Open de app via je lokale webserver in een gewone ontwikkelomgeving. In de cloud gebruiken de tests interne HTTP-verzoeken. Python 3 is voldoende om de app te serveren; Node 18+ is nodig voor de logische tests.

## Wat is gebouwd?

- Acht modulaire vragen: niveau, leerjaar (1–4), motivatie, leesvaardigheid, moeilijkheid, interesses, verhaalvoorkeuren en zes intensiteitssliders.
- Alle gevraagde interessecategorieën, maximaal twaalf interesses en een verplichte primaire interesse die dubbel meetelt.
- Negentien verhaalvoorkeuren (maximaal vijf), inclusief waargebeurd, psychologie/diepgang, feelgood, donker, sciencefiction en technologie.
- Een neutrale keuze voor moeilijkheid. Realisme, tempo, lengte en uitgesloten onderwerpen worden niet meer uitgevraagd; het leerlingprofiel gebruikt daarvoor neutrale waarden.
- Schermanimaties respecteren verminderde beweging. De engine blijft onderwerpfilters ondersteunen voor een toekomstige databron, maar de leerling kiest deze niet meer.
- Een persoonlijke top 5 met percentages, maximaal drie redenen, tags, covers en rangnummer; de eerste kaart is groter op ruime schermen.
- Samenvattingen van 40–70 woorden uitsluitend na klikken in een detailmodal, met een apart blok “Waarom dit boek bij jou past”. De modal sluit met Escape, de sluitknop of een klik buiten de inhoud.
- Directe lokale feedback en vijf andere suggesties; eerst ongeziene, niet-afgewezen boeken, herhaling alleen als onvoldoende alternatieven overblijven.
- Licht ontwerp met veel wit en zachte blauwe/paarse gradients met één grote hoofdmatch en vier compacte boekkaarten. Responsive ontwerp voor laptop, Chromebook, tablet en mobiel; zichtbare focus, labels, voortgang en native dialog.
- 98 verschillende boektitels. Dit is een redactionele testcollectie: paginatallen, leeskenmerken, thema's, leeftijdsgrenzen, locatie en beschikbaarheid zijn illustratief. Gevoelige onderwerpen zijn geen gecontroleerde volledige inhoudsclassificatie. Valideer dit bij een echte catalogusimport. Er zijn nog geen geverifieerde ISBN's of Aura-records ingevuld.

## Bestanden en verantwoordelijkheden

| Bestand                   | Functie                                                   |
| ------------------------- | --------------------------------------------------------- |
| `index.html`              | Nederlandstalige pagina en modulevolgorde                 |
| `css/styles.css`          | Responsive quiz, boekkaarten en modal                     |
| `data/books.js`           | 98 titels met rijke testmetadata en samenvattingen        |
| `js/bookRepository.js`    | Enige data-ingang voor de UI: `getBooks()`                |
| `js/questions.js`         | Losse vraagdefinities, interessegroepen en keuzelimieten  |
| `js/app.js`               | Modulaire vragen, navigatie, kaarten, modal en feedback   |
| `js/matchingEngine.js`    | Harde filters, gewogen scores, feedback en matchredenen   |
| `js/diversification.js`   | Reranking met auteur- en interessevariatie                |
| `js/coverService.js`      | Coverresolutie, verificatie, cache en lokale SVG-fallback |
| `js/state.js`             | Profiel in geheugen, feedback in sessionStorage           |
| `js/analytics.js`         | Bewust lege analytics: geen tracking                      |
| `tests/matching.test.cjs` | Data, vijf profielen, filters, diversiteit en feedback    |
| `tests/covers.test.cjs`   | Covervolgorde, titel/auteurcontrole, cache en fallback    |
| `tests/browser.test.py`   | Volledige quiz en interacties in Chromium                 |

## Matchlogica

`MATCH_WEIGHTS` is centraal configureerbaar: niveau/leesbaarheid 25%, interesses 25%, verhaalvoorkeuren 25%, leesstijl 10%, lengte 5%, sfeer 10%. `matchingEngine.evaluate()` geeft de deelscores, gewogen som, combinatiebonus, strafpunten, maximaal haalbare score en feedbackcorrectie terug.

Het percentage wordt berekend als `100 × (gewogen som + combinatiebonus − strafpunten) / maximaal haalbare score`, afgerond binnen 0–100. Alleen actieve voorkeuren tellen mee in de noemer; een neutrale keuze krijgt geen fictieve middenscore. De combinatiebonus heeft een expliciet maximum van 0,05. Feedback geeft daarna een begrensde correctie van maximaal ±15 procentpunten. Percentages zijn inhoudelijke overeenkomsten, geen voorspelde kans dat iemand het boek leuk vindt.

- Een directe interesse telt volledig mee; de primaire interesse telt dubbel. Een aantoonbaar verwante bredere interesse telt slechts 30% mee. Combinaties met gewenste sterke thema's krijgen een bonus.
- Verhaalkeuzes gebruiken de aanwezige themascores 0–5. Intensiteitssliders vergelijken hoeveelheid, inclusief straf voor bijvoorbeeld veel horror terwijl de leerling geen horror wil. Realistische voorkeuren verlagen sterk fantastische boeken extra.
- Niveau en leesvaardigheid vormen samen de leesbaarheidscomponent. Moeilijkheid en tempo tellen afzonderlijk in leesstijl. Lage motivatie geeft moeilijk/dik/traag lezen straf en weegt korte hoofdstukken, duidelijke verhaallijn, snel begin en actie mee.
- Lengte is zacht. Leerjaar telt als lichte voorkeur. Onbeschikbare boeken, totaal verkeerd niveau en uitgesloten gevoelige onderwerpen blijven altijd uitgesloten. Een optioneel taalfilter en `requireAura` staan klaar, maar Aura wordt in Fase 1 niet geactiveerd.
- Nummer 1 blijft de hoogste inhoudelijke score. De selectie voor 2–5 gebruikt de top 20, eventueel uitgebreid voor voldoende auteurs. Thematische cosinusovereenkomst en interesseoverlap sturen diversiteit. Maximaal twee bijna identieke profielen worden gekozen als er voldoende alternatieven binnen 12 scorepunten zijn; anders blijft inhoudelijke aansluiting belangrijker.
- Een kleine, sessiegebonden variatie van maximaal 1,5 rerankingpunten kiest tussen vergelijkbaar goede opties. Dezelfde seed geeft reproduceerbare resultaten. Matchpercentages zelf worden hierdoor niet aangepast.
- Feedback gebruikt thema- én interesseoverlap. Volgende rondes gebruiken eerst ongeziene boeken, dan eerder getoonde geaccepteerde boeken, en pas als noodzakelijk afgewezen boeken. De harde veiligheidsfilters blijven in elke ronde gelden.

De datastructuur bevat ook `teaser`, `fictionType`, `depth`, `narrativeClarity`, `fastStart`, `language` en `catalogSource`. Een toekomstige verrijker kan voorstellen doen voor deze velden; een beheerder moet de testmetadata en voorstellen controleren voordat ze als echte catalogusgegevens worden gebruikt.

## Covers en privacy

Volgorde: expliciete cover, ISBN-cover, Open Library-zoekresultaat, Google Books-zoekresultaat, lokale SVG-omslag. Een eerder geslaagde omslag kan vanuit de titel/auteur/ISBN-cache worden hergebruikt. Zoekresultaten moeten qua titel én auteur overeenkomen en bij een bekend ISBN ook de juiste editie bevestigen; mislukte plaatjes en time-outs gaan door naar de volgende bron. ISBN's zijn pas bruikbaar nadat de editie is gecontroleerd.

Alleen cover-URL's worden in localStorage bewaard. Antwoorden blijven in geheugen; feedback (boek-ID met +1/−1) blijft in sessionStorage en verdwijnt bij het sluiten van de browsersessie. Geen persoonsgegevens of analytics worden opgeslagen. Coverproviders ontvangen alleen titel/auteur of ISBN, nooit het leesprofiel.

In deze cloudomgeving geven live verzoeken naar Open Library en Google Books momenteel een proxy-403. De lokale fallback is echt in Chromium getest; succes van de externe coverdiensten is met gecontroleerde testantwoorden getest, niet met live diensten. Benodigde netwerkdomeinen: `openlibrary.org`, `covers.openlibrary.org`, `www.googleapis.com`, `books.google.com`, `books.googleusercontent.com`.

## Tests

Vanuit de projectmap:

```bash
node --test tests/*.test.cjs
```

Voor de browsercontrole, met de webserver op poort 8000:

```bash
python tests/browser.test.py
```

De browsertest vereist het Python-pakket Playwright en Chromium op `/usr/bin/chromium` (aanwezig in deze cloudomgeving). Voor een andere installatie kun je dat pad aanpassen. Externe coververzoeken worden in deze test bewust geweigerd om te controleren dat de app bruikbaar blijft zonder deze diensten.

Gevalideerd: 24 JavaScript-tests en 7 Python-importtests geslaagd, plus een volledige browserdoorloop zonder JavaScript-fouten. De vijf voorgeschreven profielen geven verschillende top-5's. De browsercontrole test interessevalidatie, keuzelimieten, neutrale keuzes, sliders, terugnavigatie, acht stappen, vijf kaarten, modal en Escape, feedback, nieuwe titels, sessieherstel en geen horizontale overflow bij 390, 768 en 1280 pixels. Verminderde beweging is eveneens getest.

## Eerste Aura-koppeling — openbare catalogussnapshot

De app gebruikt nu `data/aura-catalog.js`: 45 bevestigde titels uit de Bogerman-catalogus, waarvan er 40 aanwezig waren bij de controle op 8 oktober 2026. Dit is een beperkte selectie van de 98 eerder verrijkte testtitels, niet de volledige mediatheek. Een titel wordt alleen opgenomen wanneer titel en hoofdauteur overeenkomen, het materiaal een boek is en er openbare exemplaarinformatie is. Vertalerscredits en de editieaanduiding “filmeditie” worden bij die vergelijking genegeerd; andere ondertitels blijven onderscheidend. Een expliciet andere taal wordt uitgesloten. Een leeg taalveld blijft onbekend (`language: ""`), zodat geen Nederlandse taalregistratie wordt verzonnen.

`bookRepository.getBooks()` combineert de bevestigde catalogusrecords met de redactionele leeskenmerken. Onbevestigde testtitels worden niet aanbevolen. ISBN (indien uit de officiële cover herkenbaar), locatie, exemplaarstatus en cover komen uit de catalogus; niveau, pagina-indicatie, themascores en mini-samenvattingen blijven redactionele indicaties. Aura's eigen niveau wordt apart als `catalogLevel` bewaard.

Omdat de openbare HTML geen CORS-toegang biedt voor de GitHub Pages-app, gebeurt het ophalen tijdens een onderhoudsstap, niet bij iedere leerling. Een synchronisatie vervangt de snapshot alleen na een foutloze controle. Er worden geen login-, uitleen- of reserveringsacties uitgevoerd en geen persoonsgegevens opgeslagen.

Vernieuwen vanuit de projectmap:

```bash
python scripts/sync_aura.py
node --test tests/*.test.cjs
python -m unittest discover -s tests -p 'test_aura_sync.py'
```

De synchronisatie gebruikt Python's standaardbibliotheek en Node, controleert de bekende kandidaten met twee parallelle leesverzoeken en bewaart het controletijdstip. Commit en push de bijgewerkte snapshot om GitHub Pages te verversen. Er is nog geen automatische dagelijkse synchronisatie; de getoonde status is daarom nadrukkelijk die van de laatste controle. Controleer actuele beschikbaarheid altijd in Aura.

Sommige Aura-recordlinks openen zonder de bijbehorende zoeksessie een andere titel. De synchronisatie controleert daarom ook titel en auteur achter iedere directe link met een nieuwe aanvraag. Alleen een correct bevestigde link wordt als “Bekijk in Aura” gebruikt. Bij andere records opent “Open de schoolcatalogus” de algemene catalogus met de instructie daar op titel of auteur te zoeken. De bibliotheeklink staat ook op het startscherm.

Nieuwe bestanden: `scripts/sync_aura.py`, `data/aura-catalog.js`, `tests/repository.test.cjs`, `tests/test_aura_sync.py` en `.gitignore` voor Python-cachebestanden. De bestaande UI, repositorylaag, README en browsercontrole zijn bijgewerkt.

## Afbakening van de aangeleverde opdracht

Deze implementatie voert Fase 1 uit en behoudt de eerder gebouwde lokale feedback. Fase 2 heeft nu een eerste openbare snapshotkoppeling; een volledige export/API en automatische synchronisatie blijven vervolgstappen; uitgebreider feedbackleren is Fase 3; beheerinterface en anonieme analytics zijn Fase 4. Er is geen beheerlogin of externe tracking toegevoegd. De bestaande repositorystructuur is behouden en de vragen staan nu apart om toekomstige wijzigingen eenvoudiger te maken.
