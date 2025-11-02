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

## Model configuration

This app uses Google's Generative AI (Gemini). You can control which model is used
by setting the `GOOGLE_MODEL` environment variable (the code will default to
`gemini-pro-latest` if not set).

Notes and tips:
- The API may return model names prefixed with `models/` (for example `models/gemini-pro-latest`).
   The app accepts either the short name (`gemini-pro-latest`) or the full name;
   it will strip a leading `models/` automatically.
- Some models are embedding-only and won't support text generation. If you get a
   404 with a message like `not supported for generateContent`, list your available
   models (see below) and pick a non-embedding model from that list.

Quick commands
- To set the model temporarily in zsh:
```bash
export GOOGLE_MODEL=gemini-pro-latest
```

- To run the app using the project's virtualenv (recommended):
```bash
source venv/bin/activate
python3 run_app.py
```

- To list models available to your API key (run inside the same environment where
   `GOOGLE_API_KEY` is set):

```python
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
models = genai.list_models()
print([getattr(m, 'name', m.get('name', str(m))) if hasattr(m, 'get') or hasattr(m, 'name') else str(m) for m in models])
```

Security
- Do NOT commit your `.env` with API keys. If a key has been exposed, rotate it
   in Google Cloud immediately.


## License
MIT