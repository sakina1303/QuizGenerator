const app = document.querySelector('#quiz-app');
const form = document.querySelector('#quiz-form');
const cards = [...document.querySelectorAll('.question-card')];
const total = cards.length;
const progressNumber = document.querySelector('#progress-number');
const progressDial = document.querySelector('#progress-dial');
const progressHelper = document.querySelector('#progress-helper');
const finishButton = document.querySelector('#finish-button');
const finishHint = document.querySelector('#finish-hint');
const finishCard = document.querySelector('.finish-card');
const timerLabel = document.querySelector('#session-time');
const results = document.querySelector('#results');
let seconds = 0;
let finished = false;
let timer;
function startTimer() {
  timer = setInterval(() => {
    if (finished) return;
    seconds += 1;
    timerLabel.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  }, 1000);
}
startTimer();

function selectedAnswer(card) {
  return card.querySelector('input[type="radio"]:checked');
}

function updateProgress() {
  const answered = cards.filter(selectedAnswer).length;
  progressNumber.textContent = `${answered}/${total}`;
  progressDial.style.setProperty('--progress', `${answered / total * 100}%`);
  progressHelper.textContent = answered === total ? 'Ready for your results.' : answered === 0 ? "You're just getting started." : `${total - answered} to go. Keep it up.`;
  finishHint.textContent = answered === total ? 'Your study snapshot is ready.' : `Answer ${total - answered} more ${total - answered === 1 ? 'question' : 'questions'} to unlock your results.`;
  finishButton.disabled = answered !== total || finished;
  cards.forEach((card) => {
    const jump = document.querySelector(`[data-jump="${card.dataset.number}"]`);
    jump.classList.toggle('is-done', Boolean(selectedAnswer(card)));
  });
}

form.addEventListener('change', updateProgress);
updateProgress();

function addRecommendation(index, title, detail) {
  const item = document.createElement('article');
  item.className = 'recommendation';
  const number = document.createElement('span');
  number.textContent = String(index).padStart(2, '0');
  const copy = document.createElement('div');
  const heading = document.createElement('strong');
  heading.textContent = title;
  const description = document.createElement('p');
  description.textContent = detail;
  copy.append(heading, description);
  item.append(number, copy);
  document.querySelector('#recommendations').append(item);
}

function addReview(card, picked, showSelected = true) {
  const item = document.createElement('article');
  item.className = 'mistake-item';
  const label = document.createElement('span');
  label.className = 'mistake-label';
  label.textContent = `QUESTION ${String(card.dataset.number).padStart(2, '0')} · ${card.dataset.concept}`;
  const question = document.createElement('h4');
  question.textContent = card.querySelector('legend').textContent;
  const selected = document.createElement('p');
  selected.className = 'mistake-selected';
  selected.textContent = `Your answer: ${picked.closest('.answer-choice').querySelector('.answer-text').textContent}`;
  const correct = document.createElement('p');
  correct.className = 'mistake-correct';
  correct.textContent = `Correct answer: ${card.querySelector(`input[value="${card.dataset.answer}"]`).closest('.answer-choice').querySelector('.answer-text').textContent}`;
  const explanation = document.createElement('p');
  explanation.className = 'mistake-explanation';
  explanation.textContent = card.querySelector('.answer-review p').textContent;
  const tip = document.createElement('small');
  tip.textContent = `Next step: ${card.dataset.tip}`;
  item.append(label, question);
  if (showSelected) item.append(selected);
  item.append(correct, explanation, tip);
  document.querySelector('#mistake-list').append(item);
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (cards.some((card) => !selectedAnswer(card))) {
    cards.find((card) => !selectedAnswer(card)).scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  if (finished) return;
  finished = true;
  clearInterval(timer);
  let score = 0;
  const missed = [];
  const reviewList = document.querySelector('#mistake-list');
  reviewList.replaceChildren();
  cards.forEach((card) => {
    const picked = selectedAnswer(card);
    const isCorrect = picked.value === card.dataset.answer;
    if (isCorrect) score += 1;
    else {
      missed.push({ concept: card.dataset.concept, tip: card.dataset.tip });
      addReview(card, picked);
    }
    card.classList.add('is-reviewed');
    card.querySelector('.answer-review').hidden = false;
    card.querySelectorAll('.answer-choice').forEach((choice) => {
      const input = choice.querySelector('input');
      if (input.value === card.dataset.answer) choice.classList.add('is-correct');
      if (input === picked && !isCorrect) choice.classList.add('is-wrong');
      input.disabled = true;
    });
    const jump = document.querySelector(`[data-jump="${card.dataset.number}"]`);
    jump.classList.remove('is-done');
    jump.classList.add(isCorrect ? 'is-correct' : 'is-wrong');
  });

  const percent = Math.round(score / total * 100);
  if (score === total) {
    document.querySelector('#mistake-heading').textContent = 'Every answer, explained';
    document.querySelector('#mistake-intro').textContent = 'No mistakes this time. Review the reasoning behind each answer.';
    cards.forEach((card) => addReview(card, selectedAnswer(card), false));
  } else {
    document.querySelector('#mistake-heading').textContent = 'What to revisit';
    document.querySelector('#mistake-intro').textContent = `${missed.length} ${missed.length === 1 ? 'question needs' : 'questions need'} another look. Here are the right answers and the reasoning behind them.`;
  }
  document.querySelector('#review-mistakes').firstChild.textContent = score === total ? 'Review explanations ' : 'Review my mistakes ';
  document.querySelector('#score-number').textContent = `${score}/${total}`;
  document.querySelector('#score-percent').textContent = `${percent}% correct`;
  document.querySelector('#result-title').textContent = score === total ? 'You nailed it.' : percent >= 70 ? 'Looking sharp.' : 'This is how you grow.';
  document.querySelector('#result-subtitle').textContent = score === total
    ? 'You have a solid grasp of this set. Ready to stretch further?'
    : `You got ${score} right. Review the insights below, then build on what you know.`;
  progressHelper.textContent = 'Session complete. Nice work.';
  finishButton.disabled = true;
  finishCard.hidden = true;
  document.querySelector('.sidebar-note p').innerHTML = '<strong>Keep exploring.</strong> Review the explanations and try focused practice.';

  const recommendations = document.querySelector('#recommendations');
  recommendations.replaceChildren();
  let focus;
  if (missed.length) {
    document.querySelector('#coach-intro').textContent = 'Based on the questions you missed, start with these concepts:';
    const unique = [...new Map(missed.map((item) => [item.concept.toLowerCase(), item])).values()].slice(0, 3);
    unique.forEach((item, index) => addRecommendation(index + 1, item.concept, item.tip));
    focus = `Practice these concepts: ${unique.map((item) => item.concept).join(', ')}`;
  } else {
    document.querySelector('#coach-intro').textContent = 'You mastered this set. Here are a few directions to explore next:';
    let topics = [];
    try { topics = JSON.parse(app.dataset.nextTopics || '[]'); } catch { /* No next topics. */ }
    if (!Array.isArray(topics) || !topics.length) topics = [`Advanced ${app.dataset.topic}`];
    topics.slice(0, 3).forEach((topic, index) => addRecommendation(index + 1, topic, 'Make this the focus of your next study session.'));
    focus = `Explore ${topics.slice(0, 2).join(' and ')}`;
  }
  const practiceUrl = new URL(app.dataset.practiceUrl, window.location.origin);
  practiceUrl.searchParams.set('difficulty', app.dataset.difficulty);
  practiceUrl.searchParams.set('count', '5');
  practiceUrl.searchParams.set('focus', focus.slice(0, 230));
  const practice = document.querySelector('#focused-practice');
  practice.href = practiceUrl.toString();
  if (score === total) practice.firstChild.textContent = 'Explore a new direction ';
  results.hidden = false;
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const history = JSON.parse(localStorage.getItem('qai_sessions_v1') || '[]');
    const next = [{ topic: app.dataset.topic, score, total, date: new Date().toISOString() }, ...(Array.isArray(history) ? history : [])].slice(0, 8);
    localStorage.setItem('qai_sessions_v1', JSON.stringify(next));
  } catch { /* Storage is optional. */ }
});

document.querySelector('#review-mistakes').addEventListener('click', () => {
  document.querySelector('#mistake-review').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

document.querySelector('#retry-button').addEventListener('click', () => {
  finished = false;
  seconds = 0;
  timerLabel.textContent = '00:00';
  startTimer();
  cards.forEach((card) => {
    card.classList.remove('is-reviewed');
    card.querySelector('.answer-review').hidden = true;
    card.querySelectorAll('input[type="radio"]').forEach((input) => {
      input.checked = false;
      input.disabled = false;
    });
    card.querySelectorAll('.answer-choice').forEach((choice) => choice.classList.remove('is-correct', 'is-wrong'));
    document.querySelector(`[data-jump="${card.dataset.number}"]`).classList.remove('is-correct', 'is-wrong');
  });
  results.hidden = true;
  finishCard.hidden = false;
  document.querySelector('.sidebar-note p').innerHTML = '<strong>Take your time.</strong> Your study coach will connect the dots after you finish.';
  updateProgress();
  cards[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
});

document.querySelector('#share-link').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(window.location.href);
    button.textContent = '✓  Setup link copied';
  } catch {
    button.textContent = 'Copy unavailable in this browser';
  }
  setTimeout(() => { button.textContent = original; }, 2600);
});
