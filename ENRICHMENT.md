# Verrijking van de Excelcollectie

Uitgevoerd op 22 oktober 2026. Alle 1,529 Excelregels zijn verwerkt in
31 batches van maximaal 50. Het oorspronkelijke werkboek en de oorspronkelijke
JSON-import zijn ongewijzigd. Hun SHA-256 is `1eee2053d104ac6e9362732e5e17f3b3893fb2186306ad58b0eb3dac79f0b167`.

## Uitkomst

| Controle | Aantal |
| --- | ---: |
| Excelregels gecontroleerd | 1529 |
| Volledig verrijkt, inclusief geverifieerde editie | 0 |
| Gedeeltelijk verrijkt | 1435 |
| Niet verrijkt met bruikbare aanvullende gegevens | 94 |
| Passend bronrecord op titel en auteur | 1494 |
| Bron: Bogerman Aura | 1485 |
| Bron: Open Library | 9 |
| Bronfragment beschikbaar | 1398 |
| Catalogusthema beschikbaar | 1318 |
| Expliciete taalregistratie in bronrecord | 220 |
| Online inhoudelijke aanwijzingen voor matching | 1108 |
| Excelboeken die in de gecombineerde app kunnen worden aanbevolen | 1109 |

De laatste telling omvat bestaande redactionele koppelingen en respecteert
onbeschikbare exemplaren in de bestaande Aura-snapshot. Het aantal is dus niet
simpelweg de optelsom van online verrijking en oude koppelingen. De volledige app
bevat 1550 records, inclusief de behouden Aura-selectie;
1128 daarvan kunnen bij een ondersteund
profiel in aanmerking komen. Een passend individueel profiel blijft vereist.

"Gedeeltelijk" betekent dat minstens één aanvullende bronwaarde of onderbouwde
beoordeling is gevonden. Bij 35 regels ontbreekt een bevestigde bronidentiteit;
bij nog 59 is wel een record gevonden, maar geen bruikbare extra informatie.
Daarom zijn 94 regels niet verrijkt. Niet elke gedeeltelijk verrijkte titel heeft
genoeg inhoudelijke informatie om al te kunnen worden aanbevolen.

"Volledig" vereist ook een geverifieerde editie. Excel bevat alleen titel, auteur
en catalogusniveau; een overeenkomst op titel en auteur identificeert geen editie.
Daarom zijn geen nieuwe ISBN's, paginatallen, editiegebonden omslagen, Aura-ID's,
locaties of actuele beschikbaarheidsgegevens ingevuld. Die velden blijven onbekend.
Bestaande Aura-gegevens blijven herkenbaar als een oudere momentopname.

## Brongegevens en beoordelingen

- `data/library-catalog.json`: de ongewijzigde Excelimport, met alle bronwaarden.
- `data/enriched-catalog.json`: aanvullende brongegevens en beoordelingen per Excel-ID.
- `data/enrichment/batch-*.json`: de 31 herhaalbare checkpoints.
- `data/enrichment-report.json`: reproduceerbare tellingen en vijf testprofielen.
- `data/enrichment-quality-sample.json`: de gecontroleerde steekproef van 20 titels.

Elke aanvulling heeft een bron-URL, controledatum en zekerheid. Een bronfragment
(`facts.summary`, maximaal 220 tekens) en een letterlijk catalogusthema zijn
**brongegevens**, geen nieuw geschreven samenvatting. Taal wordt alleen overgenomen
als die expliciet is geregistreerd en heeft als scope het gevonden catalogusrecord.
Dat bewijst nog geen Excel-editie. Volledige beschrijvingen blijven in een lokale
cache buiten de Git-repository; de gepubliceerde database gebruikt korte fragmenten.

Interesses en verhaalthema's onder `assessments` zijn **automatische inschattingen**
met middelmatige zekerheid. Elke beoordeling bevat de gebruikte bronpassage,
bron-URL, datum en regelversie `evidence-tags-v5`. De classifier zoekt expliciete
termen in beschrijvingen en catalogusthema's; hij verzint geen verhaallijnen.
Niet genoemde eigenschappen worden niet als afwezig of als nul beschouwd.
Intensiteiten, schoolniveau, leesmoeilijkheid en een volledige gevoelige-onderwerpen-
classificatie blijven onbekend. C/D is niet omgezet naar Basis/Kader/GT.

De brede schapcategorieën Science fiction en Fantasy worden niet automatisch
specifieke genres: de beschrijving moet aanvullend bewijs bevatten. Afgewezen
categorieafleidingen krijgen een notitie. Tegenstrijdige expliciete taalwaarden
worden bewaard onder `conflicts` en niet ingevuld. In deze run zijn geen zulke
taalconflicten gevonden; dit is geen garantie dat alle brongegevens juist zijn.
De meeste records steunen op één bron, niet op onafhankelijke dubbele controle.

Google Books gaf bij de bereikbaarheidstest HTTP 429; die dienst is niet als
verrijkingsbron gebruikt. De schoolcatalogus en Open Library zijn wel werkelijk
uitgelezen. Een aantal Aura-aanvragen gaf HTTP 500; de fout is vastgelegd, met
één latere poging op lagere paralleliteit en een Open Library-fallback. Er zijn
geen logins, uitleenacties of reserveringen uitgevoerd.

## Gebruik bij aanbevelingen

De UI leest de gecombineerde collectie via
`bookRepository.getBooks({ includeUnreviewed: true })`. De oorspronkelijke
Excelwaarden blijven per boek in `excelSources`, ook na verrijking. De catalogus
blijft doorzoekbaar voor alle 1.529 regels, inclusief nog niet beoordeelde titels.

Nieuwe boeken met genoeg beschrijving en minstens één inhoudelijke aanwijzing
krijgen `matchMode: evidence`. Ze worden alleen geselecteerd bij een positieve
overeenkomst met een gekozen interesse of verhaalvoorkeur. De primaire interesse
telt dubbel. Onbekende niveau-, lengte-, tempo- en intensiteitsdimensies worden
niet gescoord en geven geen fictieve middenscore of straf.

Deze boeken tonen **Inhoudelijke aanwijzingen**, zonder matchpercentage. Een
interne, begrensde sorteerscore gebruikt uitsluitend positieve aanwijzingen,
expliciet ongewenste aanwezige thema's en lokale feedback. Dit is een rangschikking,
geen gevalideerde voorspelling van leesplezier. De modal toont bronfragment,
bronverwijzingen, onderbouwing en onbekende informatie. Ook een omslag wordt niet
via een onbevestigde editie opgehaald; er verschijnt een lokale fallback.

Als iemand expliciet gevoelige onderwerpen uitsluit, worden nieuwe boeken met een
onvolledige classificatie conservatief uitgesloten. Een expliciet taalfilter vereist
een bekende passende taal. `requireAura` blijft nieuwe records zonder bevestigde
Aura-identiteit uitsluiten. Deze filters worden in iedere suggestieronde behouden.
De bestaande quiz, twaalf interesses, lichte vormgeving, uitleg, feedback en
"vijf andere" blijven beschikbaar.

## Reproduceren en onderhoud

Vanuit `/workspace/boekenmatchV2`, met de bestaande ontwikkelomgeving:

```sh
/workspace/boekenmatch-tools/bin/python scripts/enrich_catalog.py --fallback
node scripts/catalog_report.cjs
node --test tests/*.test.cjs
/workspace/boekenmatch-tools/bin/python -m unittest discover -s tests -p 'test_*.py'
/workspace/boekenmatch-tools/bin/python tests/browser.test.py
```

De laatste opdracht vereist de bestaande webserver op poort 8000. De app heeft
geen runtime-API of geheime sleutel nodig: GitHub Pages serveert de opgeslagen
JSON. Herhaal geen netwerksynchronisatie bij iedere start van de app.

De verrijker gebruikt de Python-standaardbibliotheek en de bestaande Aura-parser.
Drie geïsoleerde Aura-sessies beperken de paralleliteit. Open Library-fallbacks
lopen achtereenvolgens, met minstens 1,1 seconde tussen aanvragen. De cache staat
in `/workspace/boekenmatch-enrichment-cache`. Een gewone herhaling gebruikt die
cache en leidt beoordelingen opnieuw af; dat is geen nieuwe broncontrole.

Voor een expliciete latere broncontrole:

```sh
/workspace/boekenmatch-tools/bin/python scripts/enrich_catalog.py --fallback --refresh
```

Bij een mislukte verversing blijft eerder bevestigde broninformatie met de oude,
werkelijke controledatum behouden; de nieuwe mislukte poging wordt toegevoegd.
`--start 0 --limit 50` beperkt een run tot een uitgelijnde batch. Gebruik hele
batches van 50; na regelwijzigingen moeten alle batches opnieuw uit de cache
worden opgebouwd. Checkpoints met een andere bronhash of regelversie mogen niet
ongemerkt worden gemengd. TLS-verificatie blijft ingeschakeld.

## Uitgevoerde kwaliteitscontrole

Een steekproef van 20 over het werkboek verspreide titels is door Codex beoordeeld
op bronidentiteit en onderbouwing in de beschrijving. Dit was geen volledige
boeklezing of beoordeling door een jeugdbibliothecaris. Daarnaast zijn de gevallen
Slagveld (beroep auteur is geen thema), Hof van mist en woede/Hades (breed schap is
geen SF-bewijs), Spotgaai (idem voor Fantasy), Neem een kip (genoemde voorgaande
titel is geen inhoudsbewijs) en Percy Jackson (een losse laatste schooldag is geen
schoolthema) gebruikt om de regels aan te scherpen en regressietests toe te voegen.

De vijf profielen geven verschillende top-vijfselecties. Ook alleen met de online
verrijkte Excelboeken levert elk profiel vijf suggesties: respectievelijk 224, 126,
194, 383 en 144 passende kandidaten. Zie het JSON-rapport voor de concrete titels.

Gevalideerd: 31 JavaScript-tests, 18 Python-tests en een volledige Chromium-
browserdoorloop. De tests controleren ook bronbehoud, herkomst, verversingsfouten,
onbekende dimensies, filters, zoeken, twaalf interesses, feedback, nieuwe suggesties,
modals, responsiviteit en weergave zonder fictief percentage. Externe covers worden
in de browsertest bewust geblokkeerd; live omslagdiensten zijn hiermee niet bewezen.
