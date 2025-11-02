import os
from dotenv import load_dotenv
load_dotenv()
# Ensure default model if not set externally
os.environ.setdefault('GOOGLE_MODEL', 'gemini-pro-latest')

import app

if __name__ == '__main__':
    # Start the Flask app on port 5002 for testing
    app.app.run(debug=True, port=5002)
