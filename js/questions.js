(function () {
  const groups = {
    Sport: [
      "voetbal",
      "Formule 1",
      "fitness",
      "vechtsport",
      "basketbal",
      "skateboarden",
      "wintersport",
    ],
    Entertainment: [
      "games",
      "social media",
      "YouTube",
      "films",
      "series",
      "muziek",
      "influencers",
      "reality-tv",
    ],
    Techniek: [
      "computers",
      "AI",
      "auto's",
      "motoren",
      "machines",
      "bouwen",
      "wetenschap",
    ],
    Mensen: [
      "vriendschap",
      "verliefdheid",
      "relaties",
      "familie",
      "school",
      "pesten",
      "identiteit",
      "volwassen worden",
    ],
    Wereld: [
      "oorlog",
      "geschiedenis",
      "criminaliteit",
      "waargebeurde verhalen",
      "rampen",
      "reizen",
    ],
    Fantasie: [
      "magie",
      "fantasy",
      "monsters",
      "superkrachten",
      "sciencefiction",
      "dystopie",
      "zombies",
      "mythologie",
    ],
    "Dieren & natuur": ["dieren", "natuur", "paarden", "honden", "survival"],
  };
  const questions = [
    {
      key: "level",
      title: "Welk niveau doe je?",
      hint: "We zoeken boeken die bij je passen. Je hoeft geen leesexpert te zijn.",
      options: [
        ["basis", "Basis"],
        ["kader", "Kader"],
        ["gt", "GT"],
      ],
    },
    {
      key: "schoolYear",
      title: "In welk leerjaar zit je?",
      options: [
        [1, "Leerjaar 1"],
        [2, "Leerjaar 2"],
        [3, "Leerjaar 3"],
        [4, "Leerjaar 4"],
      ],
    },
    {
      key: "readingMotivation",
      title: "Hoe voel jij je over lezen?",
      options: [
        [1, "😅 Liever iets anders"],
        [2, "🙂 Soms best leuk"],
        [3, "📚 Ik lees graag"],
        [4, "🔥 Geef mij maar boeken"],
      ],
    },
    {
      key: "readingDifficulty",
      title: "Hoe uitdagend mag het zijn?",
      options: [
        [1, "Lekker makkelijk"],
        [2, "Goed te volgen"],
        [3, "Een beetje uitdaging"],
        [4, "Laat me nadenken"],
      ],
    },
    {
      key: "interests",
      title: "Waar word jij enthousiast van?",
      hint: "Kies meerdere interesses en daarna één favoriet. Je favoriet telt dubbel.",
      type: "interests",
    },
    {
      key: "storyPreferences",
      title: "Wat zoek je in een verhaal?",
      hint: "Je kunt meerdere kiezen, of deze stap overslaan.",
      type: "multi",
      options: [
        "spanning",
        "humor",
        "romantiek",
        "mysterie",
        "fantasy",
        "oorlog",
        "school",
        "vriendschap",
      ].map((x) => [x, x]),
    },
    {
      key: "themes",
      title: "Stel jouw verhaal samen",
      hint: "0 = liever niet · 5 = heel veel. Lage scores tellen ook mee.",
      type: "sliders",
    },
  ];

  groups.Sport.push("andere sport");
  groups.Wereld.push("politiek", "andere landen");
  questions.splice(3, 0, {
    key: "readingAbility",
    title: "Hoe gaat lezen bij jou?",
    hint: "Dit is geen toets. Kies wat jij prettig vindt.",
    options: [
      [1, "📖 Korte, duidelijke zinnen helpen mij"],
      [2, "🙂 Gewone verhalen gaan prima"],
      [3, "🧠 Ook ingewikkelde verhalen gaan goed"],
    ],
  });
  const byKey = (key) => questions.find((q) => q.key === key);
  byKey("readingDifficulty").options.push(["any", "Maakt mij niet uit"]);
  byKey("interests").maxSelections = 12;
  byKey("interests").hint =
    "Kies maximaal 12 interesses en daarna één favoriet. Je favoriet telt dubbel.";
  byKey("storyPreferences").maxSelections = 5;
  byKey("storyPreferences").hint =
    "Kies maximaal 5 ingrediënten, of sla deze stap over.";
  byKey("storyPreferences").options = [
    ["spanning", "🔥 Spanning"],
    ["humor", "😂 Humor"],
    ["romantiek", "❤️ Liefde"],
    ["oorlog", "⚔️ Oorlog"],
    ["mysterie", "🕵️ Mysterie"],
    ["horror", "👻 Horror"],
    ["fantasy", "🐉 Fantasy"],
    ["sport", "⚽ Sport"],
    ["technologie", "🎮 Games / technologie"],
    ["vriendschap", "🤝 Vriendschap"],
    ["school", "🏫 School"],
    ["waargebeurd", "🌍 Waargebeurd"],
    ["misdaad", "🔎 Misdaad"],
    ["psychologie", "🧠 Psychologie / diepgang"],
    ["sciencefiction", "🚀 Sciencefiction"],
    ["actie", "💥 Actie"],
    ["emotioneel", "😢 Emotioneel"],
    ["donker", "🌑 Donker"],
    ["feelgood", "🌈 Feelgood"],
  ];
  window.quizConfig = { groups, questions };
})();
