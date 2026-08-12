from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_pyfile('config.py')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def normalize_model_name(name):
    if not name:
        return ''
    if name.startswith('models/'):
        return name.split('/', 1)[1]
    return name


_model = None


def load_model():
    candidates = [
        os.getenv('GOOGLE_MODEL'),
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro-latest',
    ]
    seen = set()

    for candidate in candidates:
        model_name = normalize_model_name(candidate)
        if not model_name or model_name in seen:
            continue
        seen.add(model_name)

        try:
            return genai.GenerativeModel(model_name)
        except Exception:
            continue

    return None


def get_model():
    global _model

    if _model is None:
        _model = load_model()

    return _model

def generate_quiz_prompt(topic, difficulty='medium', num_questions=5):
    return f"""
    Generate a {num_questions}-question multiple choice quiz about {topic}.
    Aim for {difficulty} difficulty.
    For each question:
    - Provide 4 possible answers (a, b, c, d)
    - Mark the correct answer with (Correct)
    - Format each question like this:
        Q1. [Question text]
        a) [Option 1]
        b) [Option 2]
        c) [Option 3]
        d) [Option 4]
        Answer: [Correct letter]
    Ensure the quiz is challenging but fair.
    Return only the quiz content, no additional commentary.
    """


def build_fallback_quiz(topic, num_questions=5):
    templates = [
        'What is the best starting point for learning about {topic}?',
        'Which idea is most closely related to {topic}?',
        'Which example would best illustrate {topic}?',
        'What is a common mistake people make when studying {topic}?',
        'Which option best summarizes the core idea of {topic}?',
    ]

    fallback_questions = []
    answers = ['a', 'b', 'c', 'd', 'a']

    for index in range(num_questions):
        fallback_questions.append({
            'number': index + 1,
            'text': templates[index % len(templates)].format(topic=topic),
            'options': [
                {'letter': 'a', 'text': f'A broad overview of {topic}.'},
                {'letter': 'b', 'text': f'A detail that is usually unrelated to {topic}.'},
                {'letter': 'c', 'text': f'A practical example of {topic} in use.'},
                {'letter': 'd', 'text': f'A deeper edge case connected to {topic}.'},
            ],
            'answer': answers[index % len(answers)],
        })

    return {
        'topic': topic,
        'questions': fallback_questions,
    }


def render_quiz(topic, questions, quiz_source):
    return render_template(
        'quiz.html',
        topic=topic,
        questions=questions,
        quiz_source=quiz_source,
    )

def parse_quiz_response(response):
    questions = []
    current_question = {}
    
    for line in response.text.split('\n'):
        line = line.strip()
        if line.startswith('Q'):
            if current_question:
                questions.append(current_question)
            current_question = {
                'question': line[line.find('.')+1:].strip(),
                'options': [],
                'answer': ''
            }
        elif line and line[0].lower() in ['a', 'b', 'c', 'd']:
            option = line[line.find(')')+1:].strip()
            if '(Correct)' in option:
                option = option.replace('(Correct)', '').strip()
                current_question['answer'] = line[0].lower()
            current_question['options'].append(option)
        elif line.lower().startswith('answer:'):
            current_question['answer'] = line.split(':')[1].strip().lower()[0]
    
    if current_question:
        questions.append(current_question)
    
    return questions

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form['topic']
        difficulty = request.form.get('difficulty', 'medium')
        return redirect(url_for('generate_quiz', topic=topic, difficulty=difficulty))
    return render_template('index.html')

@app.route('/quiz/<topic>')
def generate_quiz(topic):
    difficulty = request.args.get('difficulty', 'medium')
    model = get_model()

    if not GOOGLE_API_KEY or model is None:
        quiz_data = build_fallback_quiz(topic)
        return render_quiz(topic, quiz_data['questions'], 'Offline fallback')

    try:
        prompt = generate_quiz_prompt(topic, difficulty=difficulty)
        response = model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("Empty response from Gemini API")
            
        questions = parse_quiz_response(response)
        
        if not questions:
            raise ValueError("Failed to parse quiz questions")

        # Prepare properly structured quiz data
        quiz_data = {
            'topic': topic,
            'questions': [
                {
                    'number': i+1,
                    'text': q['question'],
                    'options': [
                        {'letter': 'a', 'text': (q['options'][0] if len(q['options']) > 0 else 'Option A')},
                        {'letter': 'b', 'text': (q['options'][1] if len(q['options']) > 1 else 'Option B')},
                        {'letter': 'c', 'text': (q['options'][2] if len(q['options']) > 2 else 'Option C')},
                        {'letter': 'd', 'text': (q['options'][3] if len(q['options']) > 3 else 'Option D')}
                    ],
                    'answer': q['answer'] or 'a'
                }
                for i, q in enumerate(questions)
            ]
        }
            
        return render_quiz(topic, quiz_data['questions'], 'Gemini')
        
    except Exception as e:
        quiz_data = build_fallback_quiz(topic)
        return render_quiz(topic, quiz_data['questions'], 'Offline fallback')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
