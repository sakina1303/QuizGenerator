import logging
import os
import re
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
import requests

load_dotenv()
app = Flask(__name__)
app.config.from_pyfile('config.py')
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Model construction is local and cannot tell whether a project has quota.
DEFAULT_MODELS = (
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash',
)


def model_candidates():
    names = (os.getenv('GOOGLE_MODEL', ''), *DEFAULT_MODELS)
    return list(dict.fromkeys(
        name.removeprefix('models/').strip()
        for name in names if name and name.strip()
    ))


def generate_quiz_prompt(topic, difficulty='medium', num_questions=5):
    return f"""Generate exactly {num_questions} multiple-choice questions about {topic}.
Difficulty: {difficulty}. Each question must have four plausible options and one
unambiguous correct answer. Use this format exactly, with no introduction:
Q1. Question text
a) Option A
b) Option B
c) Option C
d) Option D
Answer: a
Repeat for all questions. Vary the position of the correct answer."""


def parse_quiz_response(text, expected=5):
    questions = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        question_match = re.match(r'^Q\s*(\d+)\s*[.)]\s*(.+)$', line, re.I)
        option_match = re.match(r'^([a-d])\s*[).]\s*(.+)$', line, re.I)
        answer_match = re.match(r'^Answer\s*:\s*([a-d])\b', line, re.I)
        if question_match:
            if current:
                questions.append(current)
            current = {'text': question_match.group(2), 'options': [], 'answer': ''}
        elif current and option_match:
            letter, option = option_match.groups()
            if '(Correct)' in option:
                current['answer'] = letter.lower()
                option = option.replace('(Correct)', '').strip()
            current['options'].append({'letter': letter.lower(), 'text': option})
        elif current and answer_match:
            current['answer'] = answer_match.group(1).lower()
    if current:
        questions.append(current)

    if len(questions) != expected or any(
        len(q['options']) != 4
        or [option['letter'] for option in q['options']] != list('abcd')
        or q['answer'] not in 'abcd'
        for q in questions
    ):
        raise ValueError('The quiz service returned an incomplete quiz.')
    for number, question in enumerate(questions, 1):
        question['number'] = number
    return questions


def generate_questions(topic, difficulty):
    prompt = generate_quiz_prompt(topic, difficulty)
    last_status = None
    for name in model_candidates():
        try:
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{quote(name, safe="")}:generateContent',
                headers={'x-goog-api-key': GOOGLE_API_KEY},
                json={'contents': [{'parts': [{'text': prompt}]}]},
                timeout=20,
            )
        except requests.RequestException:
            logger.exception('Could not connect to Gemini')
            raise
        if response.status_code in {403, 404, 429}:
            logger.warning('Gemini model %s returned HTTP %s', name, response.status_code)
            last_status = response.status_code
            continue
        response.raise_for_status()
        try:
            parts = response.json()['candidates'][0]['content']['parts']
            text = '\n'.join(part['text'] for part in parts if 'text' in part)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ValueError('Gemini returned no quiz content.') from error
        return parse_quiz_response(text), name
    raise RuntimeError(f'No configured Gemini model could generate a quiz (HTTP {last_status}).')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        difficulty = request.form.get('difficulty', 'medium')
        if not topic:
            return render_template('index.html', error='Enter a topic to continue.'), 400
        if difficulty not in {'easy', 'medium', 'hard'}:
            difficulty = 'medium'
        return redirect(url_for('generate_quiz', topic=topic, difficulty=difficulty))
    return render_template('index.html')


@app.route('/quiz/<topic>')
def generate_quiz(topic):
    if not GOOGLE_API_KEY:
        return render_template('quiz.html', topic=topic,
                               error='Quiz generation is not configured. Set GOOGLE_API_KEY on the server.'), 503
    difficulty = request.args.get('difficulty', 'medium')
    if difficulty not in {'easy', 'medium', 'hard'}:
        difficulty = 'medium'
    try:
        questions, model_name = generate_questions(topic, difficulty)
        return render_template('quiz.html', topic=topic, questions=questions,
                               quiz_source=f'Gemini ({model_name})')
    except RuntimeError:
        return render_template('quiz.html', topic=topic,
                               error='The quiz service is out of capacity right now. Please try again later or configure a Gemini API project with available quota.'), 503
    except Exception:
        logger.exception('Could not generate quiz')
        return render_template('quiz.html', topic=topic,
                               error='Quiz generation failed. Please try again shortly.'), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
