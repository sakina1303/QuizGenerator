/* A small, private learning map kept in this browser. */
(() => {
  const KEY = 'qai_mastery_v1';
  const DAY = 24 * 60 * 60 * 1000;
  const intervals = [1, 3, 7, 14, 30];

  function read() {
    try {
      const value = JSON.parse(localStorage.getItem(KEY) || '[]');
      if (!Array.isArray(value)) return [];
      return value.filter((item) => item && typeof item.topic === 'string' &&
        typeof item.concept === 'string' && typeof item.key === 'string' &&
        Number.isFinite(item.attempts) && item.attempts > 0 &&
        Number.isFinite(item.correct) && Number.isFinite(item.dueAt)).slice(0, 250);
    } catch { return []; }
  }

  function recordQuiz(topic, answers, sourceKind = 'topic') {
    if (typeof topic !== 'string' || !Array.isArray(answers)) return false;
    const items = read();
    const now = Date.now();
    answers.forEach(({ concept, correct }) => {
      if (typeof concept !== 'string' || !concept.trim()) return;
      const label = concept.trim().slice(0, 100);
      const key = `${topic.trim().toLowerCase()}::${label.toLowerCase()}`;
      let item = items.find((candidate) => candidate.key === key);
      if (!item) {
        item = { key, topic: topic.slice(0, 120), concept: label,
          sourceKind: sourceKind === 'notes' ? 'notes' : 'topic',
          attempts: 0, correct: 0, streak: 0, lastAt: now, dueAt: now };
        items.push(item);
      }
      item.attempts += 1;
      if (correct) item.correct += 1;
      item.streak = correct ? Math.min((item.streak || 0) + 1, 100) : 0;
      item.lastAt = now;
      item.dueAt = correct ? now + intervals[Math.min(item.streak - 1, intervals.length - 1)] * DAY : now;
    });
    items.sort((a, b) => b.lastAt - a.lastAt);
    try {
      localStorage.setItem(KEY, JSON.stringify(items.slice(0, 250)));
      return true;
    } catch { return false; }
  }

  window.QAIProgress = { read, recordQuiz };
})();
