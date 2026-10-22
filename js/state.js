window.appState = {
  profile: {
    level: "kader",
    schoolYear: 3,
    readingMotivation: 2,
    readingAbility: 2,
    readingDifficulty: 2,
    interests: [],
    primaryInterest: "",
    themes: {
      spanning: 3,
      humor: 3,
      romantiek: 2,
      horror: 0,
      actie: 3,
      emotioneel: 2,
    },
    storyPreferences: [],
    realismFantasy: null,
    readingSpeed: null,
    maxPages: null,
    avoidTopics: [],
  },
  step: 0,
  seed: Math.floor(Math.random() * 0x7fffffff),
  round: 0,
  shown: new Set(),
  feedback: {},
};
try {
  appState.feedback = JSON.parse(
    sessionStorage.getItem("boekenmatch-feedback") || "{}",
  );
} catch {}
window.saveFeedback = () => {
  try {
    sessionStorage.setItem(
      "boekenmatch-feedback",
      JSON.stringify(appState.feedback),
    );
  } catch {}
};
