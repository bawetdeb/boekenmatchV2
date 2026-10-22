# BoekenMatch – instructies voor Codex

## Doel
Bouw een professionele webapp voor vmbo-leerlingen van csg Bogerman waarmee leerlingen via een korte, visuele vragenlijst een persoonlijke top 5 boeken krijgen.

De uiteindelijke mediatheekbron wordt later Aura Library:
https://bogerman.auralibrary.nl/auraicx.aspx

Werk nu eerst alleen aan **Fase 1** met testdata.

## UX
- Eén vraag per scherm.
- Voortgangsbalk.
- Moderne uitstraling: Spotify/Netflix/persoonlijkheidsquiz.
- Kleuren: rood, oranje, geel, paars.
- Goed op laptop, Chromebook, tablet en mobiel.
- Geen persoonsgegevens opslaan.

## Vragenlijst
Bouw minimaal deze stappen:
1. Niveau: Basis / Kader / GT
2. Leerjaar: 3 / 4
3. Leesmotivatie: 4 niveaus
4. Gewenste moeilijkheid
5. Interesses buiten boeken
6. Verhaalvoorkeuren
7. Intensiteit via sliders: spanning, humor, romantiek, horror, actie, emotionele zwaarte
8. Realistisch versus fantasie
9. Gewenst leestempo
10. Boeklengte
11. Onderwerpen die de leerling liever vermijdt

Maak de vragen modulair.

## Interesses
Ondersteun onder andere:
- sport: voetbal, Formule 1, fitness, vechtsport, basketbal, skateboarden, wintersport
- entertainment: games, social media, YouTube, films, series, muziek, influencers, reality-tv
- techniek: computers, AI, auto's, motoren, machines, bouwen, wetenschap
- mensen: vriendschap, verliefdheid, relaties, familie, school, pesten, identiteit, volwassen worden
- wereld: oorlog, geschiedenis, criminaliteit, waargebeurde verhalen, rampen, reizen
- fantasie: magie, fantasy, monsters, superkrachten, sciencefiction, dystopie, zombies, mythologie
- dieren/natuur: dieren, natuur, paarden, honden, survival

Laat meerdere keuzes toe en één primaire interesse die dubbel meetelt.

## Boekendata
Gebruik per boek een rijke datastructuur met o.a.:
- id, isbn, title, author
- levels, schoolYear
- readingDifficulty, readingSpeed, chapterLength, pages
- themes met scores 0–5
- interests
- realismFantasy 1–5
- ageMin, ageMax
- sensitiveTopics
- summary
- coverUrl
- auraId, auraUrl, location, available

## Matching-engine
Refactor `js/matchingEngine.js`.

Gebruik configureerbare gewichten:
```js
const MATCH_WEIGHTS = {
  level: 0.25,
  interests: 0.25,
  themes: 0.25,
  readingStyle: 0.10,
  length: 0.05,
  mood: 0.10
};
```

Regels:
- goede niveau-match: sterke bonus
- verkeerd niveau: stevige straf
- primaire interesse telt dubbel
- exacte combinaties (bijv. voetbal + spanning) moeten zwaarder wegen
- vergelijk sliders met boekthema-scores 0–5
- negatieve voorkeuren geven strafpunten
- lage leesmotivatie + moeilijk/dik/traag boek geeft straf
- lengte is meestal een zachte voorkeur

## Harde filters
Gebruik harde uitsluiting alleen voor:
- boek niet beschikbaar
- totaal verkeerd niveau
- expliciet uitgesloten gevoelig onderwerp
- later: boek niet in Aura

## Diversiteit
Na scoring: reranking/diversification.
- maximaal 1 boek per auteur in top 5 als er genoeg alternatieven zijn
- voorkom vijf bijna identieke thrillers
- nummer 1 blijft sterkste inhoudelijke match
- 2–5 mogen meer variëren

## Vijf andere
Knop: **🔄 Geef mij vijf andere**
- gebruik volgende beste matches
- toon geen reeds getoonde of afgewezen boeken tenzij noodzakelijk

## Feedback
Per boek:
- 👍 Dit lijkt me leuk
- 👎 Niks voor mij

Gebruik feedback direct om vergelijkbare boeken te verhogen/verlagen. Alleen lokaal bewaren.

## Resultatenpagina
Toon 5 boekkaarten.
Nummer 1 mag groter.
Per boek:
- cover
- titel
- auteur
- matchpercentage
- 2–3 tags
- maximaal 3 matchredenen

## Hover en klik
Hover:
- inhoudelijke mini-samenvatting van 40–70 woorden
- hoofdpersoon + beginsituatie + centraal probleem
- geen spoilers

Klik:
- modal met grote cover, titel, auteur, matchpercentage, samenvatting, matchredenen, niveau, pagina's, thema's, locatie, beschikbaarheid en knop 'Bekijk in Aura'.

## Covers
Refactor `js/coverService.js`.
Volgorde:
1. expliciete coverUrl
2. ISBN-gebaseerde cover
3. Open Library
4. Google Books
5. nette lokale fallback

Controleer titel + auteur en cache resultaten in localStorage.

## Architectuur
Behoud en breid modulair uit:
```text
css/styles.css
js/app.js
js/matchingEngine.js
js/diversification.js
js/bookRepository.js
js/coverService.js
js/state.js
js/analytics.js
data/books.js
```

De UI mag alleen `bookRepository.getBooks()` gebruiken.

## Testdata
Breid `data/books.js` uit naar ongeveer 100 realistische jeugdboeken met voldoende variatie in niveau, moeilijkheid, lengte, spanning, liefde, oorlog, fantasy, humor, sport, games, school, waargebeurd, horror, geschiedenis en vriendschap.

## Testprofielen
Controleer minimaal:
1. Basis + weinig leesmotivatie + voetbal + spanning + dun boek
2. Kader + games + mysterie + snel tempo
3. GT + oorlog + geschiedenis + moeilijk boek
4. Kader + liefde + school + emotioneel
5. Basis + humor + makkelijk lezen

Deze profielen moeten duidelijk verschillende top-5's geven.

## Fase 1 – voer dit nu uit
Bouw nu:
- complete vragenlijst
- uitgebreide boekdata
- betere matching-engine
- diversificatie
- top 5
- covers
- inhoudelijke mini-samenvattingen
- detailmodal
- feedbackknoppen
- vijf andere
- responsive ontwerp
- lokale tests

Werk daadwerkelijk in de bestanden. Schrijf niet alleen uitleg. Test de applicatie en los fouten op. Werk `README.md` bij met gewijzigde bestanden, matchlogica, starten van de app en welke onderdelen klaar zijn voor Aura.
