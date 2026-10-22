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

De app laadt zowel de oorspronkelijke Excelimport als `data/enriched-catalog.json`
via `bookRepository.getBooks({ includeUnreviewed: true })`. Alle 1.529 regels zijn
online onderzocht in 31 batches: 1.435 gedeeltelijk verrijkt, 94 zonder bruikbare
aanvulling. In de gecombineerde app kunnen 1.109 Excelboeken bij een passend
profiel meedoen. Onbekende dimensies blijven onbekend; nieuwe broninschattingen
geven geen matchpercentage. Bronverwijzingen en onderbouwing staan in de app.

Zie [ENRICHMENT.md](ENRICHMENT.md) voor methoden, beperkingen en de steekproef.
`node scripts/catalog_report.cjs` reproduceert tellingen en vijf testprofielen.
Voer de netwerkverrijking niet bij iedere app-start uit: de opgeslagen JSON is
voldoende voor ontwikkeling en GitHub Pages. Na een bewuste bronupdate moet het
rapport opnieuw worden gegenereerd en de bestaande tests opnieuw worden gedraaid.

Gevalideerd na verrijking: 31 JavaScript-tests, 18 Python-tests en de volledige
browsertest, inclusief zoeken, paginering, onbekende niveaus, bronvermelding,
feedback, nieuwe boeken zonder percentage en drie schermbreedtes.
