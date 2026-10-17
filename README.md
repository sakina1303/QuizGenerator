# QAI Quiz Generator

A Flask study studio that turns a topic into an interactive quiz and a focused
learning path using the Gemini API.

## Features

- Choose a topic, optional learning focus, difficulty, and 5, 8, or 10 questions.
- Take the quiz with live progress, a session timer, and a scored review.
- Read AI-generated explanations and study tips for every question.
- Get next-step recommendations based on the concepts missed, or related topics
  when the set is complete.
- Start targeted follow-up practice and see recent scores saved in this browser.
- Ask the AI tutor to simplify an answer, give an example, show its reasoning, or
  answer a follow-up question after completing a quiz.
- Track concepts across quizzes in a browser-local learning map with suggested
  revision dates and direct practice links.
- Upload a text-based PDF, TXT, or Markdown file to make a quiz from your own
  notes. Each answer includes a checked excerpt and page or section reference.

Recent scores and the learning map are stored in local browser storage on the
current device. No account or database is required. Uploaded notes are read in
memory and sent to Gemini to generate the quiz; the app does not save the file.
Notes quizzes need a new upload for another generated set. Topic quiz setup
links generate a new set rather than sharing the exact questions.

Notes files are limited to 2 MB, text-based PDFs to 20 pages, and extracted
content to 28,000 characters. Scanned PDFs without selectable text are not
supported.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Create a `.env` file with `GOOGLE_API_KEY=your_key`.
3. Run `python app.py` and open http://localhost:5000.

Keep `.env` out of Git. On Render, set `GOOGLE_API_KEY` as a service environment
variable and deploy the latest commit. The `Procfile` starts Gunicorn.

## Model and quota behavior

Set `GOOGLE_MODEL` to prefer a model available to your Gemini API project. The
app then tries `gemini-3.1-flash-lite`, `gemini-2.5-flash-lite`, and
`gemini-2.5-flash` if the preferred model returns a quota or unavailable-model
error. A successful API response is required before a quiz is shown.

Model availability and quotas differ by project. If every candidate has zero
quota, the app shows a short service message. Check your project's active limits
in Google AI Studio or use a project with available quota. A new API key from the
same project does not increase that project's quota.

The app uses the server-side `GOOGLE_API_KEY`; do not put a key in browser code
or commit it to the repository.
