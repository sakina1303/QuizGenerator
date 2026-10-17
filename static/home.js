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

const notesForm = document.querySelector('#notes-form');
notesForm?.addEventListener('submit', (event) => {
  const file = document.querySelector('#notes-file').files[0];
  if (file && file.size > 2 * 1024 * 1024) {
    event.preventDefault();
    let alert = notesForm.querySelector('.alert');
    if (!alert) {
      alert = document.createElement('div');
      alert.className = 'alert';
      alert.setAttribute('role', 'alert');
      notesForm.prepend(alert);
    }
    alert.textContent = 'Keep the notes file under 2 MB.';
    alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  const submit = notesForm.querySelector('.submit-button');
  submit.disabled = true;
  submit.querySelector('.submit-label').textContent = 'Reading your notes…';
});

if (notesForm?.querySelector('.alert')) {
  document.querySelector('#notes-builder').scrollIntoView({ block: 'start' });
}

const map = window.QAIProgress?.read() || [];
if (map.length) {
  const section = document.querySelector('#learning-map');
  const summary = document.querySelector('#map-summary');
  const list = document.querySelector('#map-list');
  const due = map.filter((item) => item.dueAt <= Date.now());
  const summaryText = document.createElement('p');
  summaryText.textContent = `${map.length} concepts tracked · ${due.length} ready to revisit`;
  summary.append(summaryText);
  const ranked = [...map].sort((a, b) =>
    Number(b.dueAt <= Date.now()) - Number(a.dueAt <= Date.now()) ||
    a.correct / a.attempts - b.correct / b.attempts || b.lastAt - a.lastAt).slice(0, 6);
  ranked.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'map-item';
    const copy = document.createElement('div');
    const tag = document.createElement('span');
    tag.textContent = item.dueAt <= Date.now() ? 'READY TO REVISIT' : 'BUILDING MASTERY';
    const title = document.createElement('strong');
    title.textContent = item.concept;
    const detail = document.createElement('small');
    detail.textContent = `${item.topic} · ${item.correct}/${item.attempts} correct`;
    copy.append(tag, title, detail);
    const link = document.createElement('a');
    if (item.sourceKind === 'notes') {
      link.href = '/#notes-builder';
      link.textContent = 'Reupload notes ↗';
    } else {
      const url = new URL(`/quiz/${encodeURIComponent(item.topic)}`, window.location.origin);
      url.searchParams.set('difficulty', 'medium');
      url.searchParams.set('count', '5');
      url.searchParams.set('focus', `Practice ${item.concept}`);
      link.href = url.toString();
      link.textContent = 'Practice ↗';
    }
    copy.append(link);
    card.append(copy);
    list.append(card);
  });
  section.hidden = false;
}

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
