# AI Quiz Generator

A web application that generates quizzes on any topic using Google's Gemini AI.

## Features
- Generate 5-question multiple choice quizzes on any topic
- Clean, responsive interface
- Powered by Google's Gemini AI

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quiz-generator.git
   cd quiz-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser to `http://localhost:5000`

## Configuration
- Edit `config.py` for Flask settings
- The `.env` file stores sensitive information (make sure to add it to `.gitignore`)

## License
MIT