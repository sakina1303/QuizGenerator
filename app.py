from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# Allow the model to be configured via environment variable for flexibility.
# If not set, default to a broadly available model name for the Google Generative AI
# python client. Change this to a different model if you have access to Gemini
# variants (for example: 'gemini-1.5-pro-latest') and your account supports it.
# Prefer a Gemini model that's commonly available on many accounts. Use the
# GOOGLE_MODEL env var to override. The list_models output uses names like
# "models/gemini-pro-latest"; the client expects the short name (e.g. "gemini-pro-latest").
MODEL_NAME = os.getenv('GOOGLE_MODEL', 'gemini-pro-latest')
genai.configure(api_key=GOOGLE_API_KEY)

# Normalize model name: if the user copied the full name returned by ListModels
# (which starts with "models/"), strip that prefix so the client doesn't end up
# sending "models/models/..." to the server.
if MODEL_NAME.startswith('models/'):
    MODEL_NAME = MODEL_NAME.split('/', 1)[1]

try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception:
    # If model construction fails, fall back to a known Gemini short name.
    # The real error (unsupported model) will surface during generate_content
    # and we already added handling that attempts to list available models.
    model = genai.GenerativeModel('gemini-pro-latest')

def generate_quiz_prompt(topic, num_questions=5):
    return f"""
    Generate a {num_questions}-question multiple choice quiz about {topic}.
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
        return redirect(url_for('generate_quiz', topic=topic))
    return render_template('index.html')

@app.route('/quiz/<topic>')
def generate_quiz(topic):
    try:
        prompt = generate_quiz_prompt(topic)
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
                        {'letter': 'a', 'text': q['options'][0]},
                        {'letter': 'b', 'text': q['options'][1]},
                        {'letter': 'c', 'text': q['options'][2]},
                        {'letter': 'd', 'text': q['options'][3]}
                    ],
                    'answer': q['answer']
                }
                for i, q in enumerate(questions)
            ]
        }
            
        return render_template('quiz.html', **quiz_data)
        
    except Exception as e:
        # If the error is caused by an unsupported/unknown model, attempt to list
        # available models to aid debugging. Listing may fail if the API key lacks
        # permissions; handle that gracefully.
        extra = ''
        try:
            models = genai.list_models()
            # models might be a list of dicts or objects depending on the library
            names = []
            for m in models:
                if isinstance(m, dict) and 'name' in m:
                    names.append(m['name'])
                else:
                    try:
                        names.append(str(m.name))
                    except Exception:
                        names.append(str(m))
            extra = '\nAvailable models: ' + ', '.join(names)
        except Exception:
            extra = '\n(while attempting to list models, listing failed)'

        return render_template('quiz.html', error=f"{e}{extra}", topic=topic)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Using port 5001 to avoid conflicts