# Omslagen voor BoekenMatch

De app gebruikt lokaal opgeslagen omslagen uit bevestigde catalogusrecords.

Gecontroleerd op 22 oktober 2026: **1468 van de 1.529 Excelregels**
hebben een gekoppelde omslag. Van de 1.109 Excelboeken die bij een passend profiel
kunnen worden aanbevolen, hebben er **1095** een
lokale omslag. Alle 25 posities in de vijf bestaande testprofielen hebben een lokale
afbeelding. Voor de overige 61 Excelregels blijft de neutrale omslag staan.
Er zijn 1496 unieke geselecteerde afbeeldingen.
Bij iedere afbeelding zijn bronpagina, oorspronkelijke afbeeldings-URL,
controledatum, overeenkomende titel/auteur, afmetingen en SHA-256 bewaard in
`data/cover-catalog.json`. `data/cover-report.json` bevat de tellingen en de
omslagdekking van de vijf bestaande testprofielen.

## Wat de afbeelding bevestigt

Titel en hoofdauteur moeten overeenkomen met het boekrecord. Voor de schoolbron
moet het materiaal bovendien een **boek** zijn. Series, deeltjes en ondertitels
blijven onderscheidend. Vertalerscredits worden alleen voor de auteursvergelijking
buiten beschouwing gelaten; de oorspronkelijke Excelwaarden blijven behouden.

Een omslag uit het schoolrecord krijgt de vermelding **Schoolcatalogus · druk kan
afwijken**. De afbeelding is daadwerkelijk bij dat titel/auteur-record aangetroffen,
maar bewijst niet welke druk van het boek uit Excel op de plank staat. Bij meerdere
catalogusomslagen toont de detailweergave aanklikbare varianten. Er wordt geen ISBN
uit een afbeelding of bestandsnaam afgeleid en er worden geen boekgegevens gewijzigd.
Een Open Library-omslag wordt als **Voorbeeldomslag · druk kan afwijken** aangeduid.

## Controle en weergave

- Een gevonden URL alleen is onvoldoende: de afbeelding is gedownload en door Pillow
  volledig als afbeelding gecontroleerd, met bruikbare afmetingen en beeldverhouding.
- HTML-foutpagina's, miniatuur/placeholders en vrijwel lege afbeeldingen worden
  afgewezen. Dezelfde afbeelding bij verschillende werken wordt niet automatisch gebruikt.
  Visueel bevestigde uitzonderingen gelden alleen voor het werkelijk afgebeelde werk.
- Bestanden staan met hun inhoudshash onder `assets/covers`. Ze worden ongewijzigd
  opgeslagen; er zijn geen omslagen gegenereerd of boekgegevens in afbeeldingen verzonnen.
- De browser gebruikt eerst de gecontroleerde lokale afbeelding, ook voor de nieuwe
  Excelboeken. Een nieuwe hash voorkomt dat een oude cache een gewijzigde omslag verbergt.
- De hele omslag blijft zichtbaar (`object-fit: contain`), zowel op de kaart als in de
  detailweergave. Een korte tekst waarschuwt dat een andere druk kan afwijken.
- Als geen betrouwbare afbeelding beschikbaar is, blijft de bestaande lokale SVG-omslag
  staan. Een ontbrekende omslagcatalogus of kapot plaatje blokkeert de quiz niet.

De ruwe Excelimport en de online tekstverrijking blijven ongewijzigd. De omslagcatalogus
is een aparte laag; een voorbeeldomslag wordt niet ten onrechte als geverifieerde
editie in de oorspronkelijke boekgegevens gezet. De JSON-bestanden en lokale plaatjes
werken via GitHub Pages zonder runtime-API, token of externe afbeeldingsaanvragen
voor boeken met een lokale omslag.

## Onderhoud

Vanuit `/workspace/boekenmatchV2`:

```sh
/workspace/boekenmatch-tools/bin/python -m pip install -r requirements-dev.txt
/workspace/boekenmatch-tools/bin/python scripts/collect_covers.py
/workspace/boekenmatch-tools/bin/python scripts/collect_covers.py --fallback
node scripts/cover_report.cjs
node --test tests/*.test.cjs
/workspace/boekenmatch-tools/bin/python -m unittest discover -s tests -p 'test_*.py'
/workspace/boekenmatch-tools/bin/python tests/browser.test.py
/workspace/boekenmatch-tools/bin/python tests/covers.browser.test.py
```

De schoolcatalogus wordt met drie gescheiden sessies uitgelezen. De tweede opdracht
met `--fallback` hergebruikt gevonden schoolomslagen en probeert Open Library alleen
voor de resterende titels; API-aanvragen worden begrensd. De cache staat buiten de
checkout in `/workspace/boekenmatch-cover-cache`. Een herhaling gebruikt bestaande
resultaten en is geen nieuwe controle van ieder bronrecord. TLS-controles blijven aan.

Voor normaal starten is verzamelen niet nodig: serveer de bestaande checkout met
`python3 -m http.server 8000 --bind 127.0.0.1`. De browsercontrole vereist die server.
De afbeeldingstests controleren ieder geselecteerd lokaal bestand op hash,
decodeerbaarheid en titel/auteur-herkomst. De browsertest blokkeert externe HTTPS-
afbeeldingen en controleert dat de nieuwe Excelboeken toch een echte lokale omslag
kunnen tonen. Een visuele steekproef controleert ook de gedrukte titel en auteur.


## Visuele kwaliteitscontrole

Een eerste steekproef van 16 en een tweede, over de Excelcollectie verspreide
steekproef van 19 omslagen zijn bekeken op gedrukte titel en auteur. Alle 11
Open Library-afbeeldingen en de niet-geselecteerde gedeelde afbeeldingen zijn ook
bekeken. Daarbij werd de Duitse omslag *Rettungslos* bij *Blauw water* afgewezen
en vervangen door de opnieuw opgehaalde Nederlandse schoolomslag.

Vijf eerder gedeelde afbeeldingen zijn na controle van gedrukte titel/auteur en
een nieuwe catalogusaanvraag alleen voor het juiste werk toegelaten: *Blauw water*,
*De bliksemdief*, *Zwarte zwaan*, *Antsy does time* en *Kapot* van Carry Slee.
De andere boeken met eenzelfde titel maar andere auteur krijgen die afbeelding
niet. `data/cover-review.json` bewaart de goedkeuringen, afwijzingen, bronnen en
controledatums; de verzamelaar past deze ook bij een herhaling toe.

Gevalideerd na koppeling: 37 JavaScript-tests, 23 Python-tests, de volledige quiz-browsertest en de aparte omslagvariant-browsertest. Alle geselecteerde afbeeldingen zijn op decodeerbaarheid, afmetingen en bestandshash gecontroleerd.
