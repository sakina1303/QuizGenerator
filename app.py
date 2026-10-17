import json
import logging
import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for


load_dotenv()
app = Flask(__name__)
app.config.from_pyfile('config.py')
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DEFAULT_MODELS = (
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
    'gemini-2.5-flash',
)
DIFFICULTIES = {'easy', 'medium', 'hard'}
QUESTION_COUNTS = {5, 8, 10}


class ModelUnavailable(Exception):
    """Every configured model was unavailable for this API project."""


def model_candidates():
    names = (os.getenv('GOOGLE_MODEL', ''), *DEFAULT_MODELS)
    return list(dict.fromkeys(
        name.removeprefix('models/').strip()
        for name in names if name and name.strip()
    ))


def clean_settings(source):
    topic = source.get('topic', '').strip()
    if not topic or len(topic) > 120:
        raise ValueError('Enter a topic of up to 120 characters.')
    difficulty = source.get('difficulty', 'medium')
    if difficulty not in DIFFICULTIES:
        difficulty = 'medium'
    try:
        count = int(source.get('count', 5))
    except (TypeError, ValueError):
        count = 5
    if count not in QUESTION_COUNTS:
        count = 5
    focus = source.get('focus', '').strip()
    if len(focus) > 240:
        raise ValueError('Keep the learning focus under 240 characters.')
    return topic, difficulty, count, focus


def generate_quiz_prompt(topic, difficulty, count, focus):
    focus_line = f'Learning focus: {focus}' if focus else 'Cover the most useful ideas in the topic.'
    return f"""Create an original, accurate {count}-question multiple-choice quiz for a learner.
Topic: {topic}
Difficulty: {difficulty}
{focus_line}

Return ONLY a JSON object, no Markdown. Use this structure:
{{"summary":"one sentence setting up the quiz","questions":[
  {{"question":"specific question","options":["choice A","choice B","choice C","choice D"],
    "answer_index":0,"explanation":"why this answer is right and the key misconception",
    "concept":"short skill label","study_tip":"one concrete thing to review if missed"}}
],"next_topics":["specific related topic","another related topic","a third related topic"]}}

Rules: exactly {count} distinct questions; exactly four plausible options for each;
one unambiguous answer_index from 0 to 3; vary the correct-answer position;
explanations must teach, not just restate the answer; avoid trick questions.
Return no facts you are uncertain of."""


def call_gemini(prompt):
    if not GOOGLE_API_KEY:
        raise ModelUnavailable('Missing GOOGLE_API_KEY')
    for name in model_candidates():
        response = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{quote(name, safe="")}:generateContent',
            headers={'x-goog-api-key': GOOGLE_API_KEY},
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'responseMimeType': 'application/json',
                    'temperature': 0.65,
                    'maxOutputTokens': 6000,
                },
            },
            timeout=60,
        )
        if response.status_code in {403, 404, 429, 500, 502, 503, 504}:
            logger.warning('Gemini model %s returned HTTP %s', name, response.status_code)
            continue
        response.raise_for_status()
        try:
            parts = response.json()['candidates'][0]['content']['parts']
            text = ''.join(part.get('text', '') for part in parts)
            return json.loads(text), name
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError('Gemini returned an unreadable quiz.') from error
    raise ModelUnavailable('No model had available quota or access.')


def validate_quiz(data, count):
    if not isinstance(data, dict) or not isinstance(data.get('questions'), list):
        raise ValueError('Gemini returned an incomplete quiz.')
    if len(data['questions']) != count:
        raise ValueError('Gemini returned the wrong number of questions.')
    questions = []
    for number, item in enumerate(data['questions'], 1):
        if not isinstance(item, dict):
            raise ValueError('Gemini returned an invalid question.')
        prompt = item.get('question')
        options = item.get('options')
        answer_index = item.get('answer_index')
        explanation = item.get('explanation')
        concept = item.get('concept')
        study_tip = item.get('study_tip')
        if (
            not isinstance(prompt, str) or not prompt.strip()
            or not isinstance(options, list) or len(options) != 4
            or any(not isinstance(option, str) or not option.strip() for option in options)
            or type(answer_index) is not int or answer_index not in range(4)
            or not isinstance(explanation, str) or not explanation.strip()
            or not isinstance(concept, str) or not concept.strip()
            or not isinstance(study_tip, str) or not study_tip.strip()
        ):
            raise ValueError('Gemini returned an invalid question.')
        questions.append({
            'number': number,
            'text': prompt.strip(),
            'options': [
                {'letter': letter, 'text': option.strip()}
                for letter, option in zip('abcd', options)
            ],
            'answer': 'abcd'[answer_index],
            'explanation': explanation.strip(),
            'concept': concept.strip(),
            'study_tip': study_tip.strip(),
        })
    next_topics = data.get('next_topics', [])
    if not isinstance(next_topics, list):
        next_topics = []
    next_topics = [topic.strip() for topic in next_topics
                   if isinstance(topic, str) and topic.strip()][:3]
    summary = data.get('summary', '')
    return {
        'summary': summary.strip() if isinstance(summary, str) else '',
        'questions': questions,
        'next_topics': next_topics,
    }


def generate_questions(topic, difficulty, count, focus):
    data, model = call_gemini(generate_quiz_prompt(topic, difficulty, count, focus))
    return validate_quiz(data, count), model


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            topic, difficulty, count, focus = clean_settings(request.form)
        except ValueError as error:
            return render_template('index.html', error=str(error), form=request.form), 400
        return redirect(url_for('generate_quiz', topic=topic, difficulty=difficulty,
                                count=count, focus=focus))
    return render_template('index.html', form=request.args)


@app.route('/quiz/<path:topic>')
def generate_quiz(topic):
    settings = {
        'topic': topic,
        'difficulty': request.args.get('difficulty', 'medium'),
        'count': request.args.get('count', 5),
        'focus': request.args.get('focus', ''),
    }
    try:
        topic, difficulty, count, focus = clean_settings(settings)
    except ValueError as error:
        return render_template('quiz.html', error=str(error)), 400
    if not GOOGLE_API_KEY:
        return render_template('quiz.html',
                               error='Quiz generation is not configured. Set GOOGLE_API_KEY on the server.'), 503
    try:
        quiz, model = generate_questions(topic, difficulty, count, focus)
        return render_template('quiz.html', topic=topic, difficulty=difficulty,
                               count=count, focus=focus, quiz=quiz, model=model)
    except ModelUnavailable:
        return render_template('quiz.html',
                               error='The quiz service is out of capacity. Please try again later.'), 503
    except (requests.RequestException, ValueError):
        logger.exception('Could not generate quiz')
        return render_template('quiz.html',
                               error='The quiz could not be generated. Please try again.'), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
