# QAI Quiz Generator

A Flask app that generates five multiple-choice questions using the Gemini API.

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
