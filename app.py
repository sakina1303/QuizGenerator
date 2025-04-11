from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

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
        return render_template('quiz.html', error=str(e), topic=topic)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Using port 5001 to avoid conflicts