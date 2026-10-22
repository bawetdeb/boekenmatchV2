# BoekenMatchV2: overname en ontwikkeling

De doelrepository was vooraf leeg (alleen de lege initialisatiecommit).
Projectbestanden zijn zonder Git-metadata overgenomen uit `bawetdeb/boekenmatch`
op `main`, commit `52fa63a84a7013cf11d88fbcc9403307f52d68d0`.
De oorspronkelijke repository is niet gewijzigd; origin blijft boekenmatchV2.
CODEX_INSTRUCTIONS.md en README.md zijn volledig gelezen. De bestaande app,
lichte vormgeving, twaalf interesses en aanbevelingsuitleg zijn behouden.

## Installeren en starten

Gebruik de bestaande checkout; maak geen extra Git-worktree.
Python 3.12, Node 18+ en systeem-Chromium op `/usr/bin/chromium` zijn vereist.
Deze cloudmachine bevat die hulpmiddelen al. De app is statisch en heeft geen
backend, npm-installatie of buildstap nodig.

```sh
cd /workspace/boekenmatchV2
python3 -m venv /workspace/boekenmatch-tools
/workspace/boekenmatch-tools/bin/python -m pip install -r requirements-dev.txt
python3 -m http.server 8000 --bind 127.0.0.1
```

Voer in een tweede terminal de controles uit:

```sh
cd /workspace/boekenmatchV2
node --test tests/*.test.cjs
/workspace/boekenmatch-tools/bin/python -m unittest discover -s tests -p 'test_*.py'
/workspace/boekenmatch-tools/bin/python tests/browser.test.py
```

De browsertest doorloopt de quiz en controleert onder meer keuzelimieten,
aanbevelingen, uitleg, modal, feedback, alternatieven en drie schermbreedtes.
Externe covers worden daarin bewust geblokkeerd; live coverdiensten zijn daarmee
niet gevalideerd. De lokale fallback wordt wel getest. Een live Aura-synchronisatie
is optioneel onderhoud en geen installatievoorwaarde; die is niet uitgevoerd.

## Excel als basisdatabase

`data/sources/jeugdboeken.xlsx` is het ongewijzigde aangeleverde bestand
“Lijst Jeugdboeken.xlsx”. `data/library-catalog.json` bevat alle 1.529 bronregels,
inclusief werkblad, Excel-rijnummer, oorspronkelijke waarden en SHA-256 van het
bronbestand. Duplicaten worden niet stilzwijgend samengevoegd of verwijderd.
Herhaal de import met:

```sh
/workspace/boekenmatch-tools/bin/python scripts/import_excel.py
```

Titel, auteur en catalogusniveau komen uit Excel. Vier niveaus ontbreken.
De catalogusniveaus C/D zijn niet omgezet naar Basis/Kader/GT. Alle ontbrekende
boekkenmerken zijn `null` en staan in `missingFields`; er zijn geen ISBN's,
samenvattingen, interesses, beschikbaarheid of andere boekgegevens verzonnen.
De oorspronkelijke bronwaarden blijven ook bij lege velden bewaard.

De app laadt deze basisdatabase nu via `bookRepository.getBooks({ includeUnreviewed:
true })`. Op het startscherm opent “Bekijk de boekendatabase” een doorzoekbare
catalogus met titel, auteur, catalogusniveau, bronrij en ontbrekende informatie.
Er zijn zoek- en niveaufilters en een knop om meer resultaten te tonen.

Alle 1.529 bronregels blijven behouden. Alleen unieke overeenkomsten op volledige
titel en auteur worden gekoppeld (auteurwoorden mogen in achternaam-eerstnotatie
staan). Er wordt niet op ongeveer gelijke titels gekoppeld en C/D wordt niet
omgezet naar een schoolniveau. Van de bronregels zijn er 24 aan bestaande
Aura-boeken gekoppeld. Nog 2 regels hebben een overeenkomst met bestaande
redactionele leeskenmerken uit `data/books.js`; die boeken kunnen nu ook worden
aanbevolen. Hun beschikbaarheid, locatie en editie blijven onbekend. De modal
vermeldt expliciet dat leeskenmerken redactioneel zijn en niet uit Excel komen.

De gecombineerde database heeft 1.550 records: 45 bestaande Aura-boeken en 1.505
extra Excelregels. De overige 1.503 Excelregels zijn doorzoekbaar maar worden
niet gescoord, omdat matchkenmerken ontbreken. De oorspronkelijke JSON-bron blijft
ongewijzigd; verrijking gebeurt bij het laden, met brongegevens in `excelSources`
en bij redactionele koppelingen `metadataSource`. Originele ontbrekende velden
blijven zichtbaar. Er worden geen nieuwe boekgegevens gegenereerd.

Gevalideerd na aansluiting: 28 JavaScript-tests, 9 Python-tests en de volledige
browsertest, inclusief zoeken, paginering, ontbrekende niveaus en responsiviteit
van de catalogus. Live verrijking via externe diensten is niet uitgevoerd.
