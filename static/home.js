const topicInput = document.querySelector('#topic');
document.querySelectorAll('[data-topic]').forEach((button) => {
  button.addEventListener('click', () => {
    topicInput.value = button.dataset.topic;
    topicInput.focus();
  });
});

const builder = document.querySelector('#quiz-builder');
builder?.addEventListener('submit', () => {
  const submit = builder.querySelector('.submit-button');
  submit.disabled = true;
  submit.querySelector('.submit-label').textContent = 'Creating your session…';
});

try {
  const sessions = JSON.parse(localStorage.getItem('qai_sessions_v1') || '[]');
  if (Array.isArray(sessions) && sessions.length) {
    const section = document.querySelector('#recent-sessions');
    const list = document.querySelector('#history-list');
    sessions.slice(0, 3).forEach((session) => {
      if (typeof session.topic !== 'string' || typeof session.score !== 'number' || typeof session.total !== 'number') return;
      const item = document.createElement('div');
      item.className = 'history-item';
      const copy = document.createElement('div');
      const title = document.createElement('strong');
      title.textContent = session.topic;
      const meta = document.createElement('small');
      meta.textContent = new Date(session.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
      const score = document.createElement('b');
      score.textContent = `${session.score}/${session.total}`;
      copy.append(title, meta);
      item.append(copy, score);
      list.append(item);
    });
    if (list.children.length) section.hidden = false;
  }
} catch {
  // Browsers can disable local storage. Quiz creation still works without it.
}
