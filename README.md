# Math Sequence Guessing Game

A modern math-sequence game with a Flask/Python backend, HTML/CSS/JavaScript frontend, SQLite history and statistics, and an optional native desktop window.

## Features

- Fibonacci and powers sequence modes
- Configurable question count and time limit
- Configurable base for powers mode
- Live countdown and immediate answer feedback
- Score summary with correct, incorrect, skipped, and accuracy totals
- Persistent SQLite game history and statistics
- Browser-based web application
- Optional desktop application using PyWebView

## Requirements

- Python 3.9 or newer
- pip

## Setup

Open a terminal in this project folder.

### Web application

```bash
python -m venv .venv
```

Activate the environment:

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install web dependencies:
```bash
pip install -r requirements-web.txt
```

Start the app:
```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

### Desktop application

Install desktop dependencies:
```bash
pip install -r requirements.txt
```

Launch:
```bash
python desktop.py
```

PyWebView uses the same Flask app and SQLite database as the web version.

## Project structure

```text
math_sequence_guessing_game/
├── app.py
├── game_engine.py
├── database.py
├── desktop.py
├── requirements.txt
├── requirements-web.txt
├── game_history.db        # created automatically
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── styles.css
└── tests/
    └── test_game_engine.py
```

## Game rules and scoring

- Fibonacci starts with the known terms `0, 1`; the first expected answer is `1`.
- Powers starts at exponent zero; the first expected answer is `base ** 0`, which is `1`.
- The sequence advances after every submitted answer, whether correct or incorrect.
- The game ends when all questions are answered or the time limit expires.
- Unanswered questions are counted as skipped.
- Accuracy is `correct answers / configured questions * 100`, matching the denominator used by the original program.

## Data storage

Game history is stored in `game_history.db` in the project folder. The database is created automatically on first launch. Keep this file to preserve results; back it up before moving or deleting the project.

## Notes

- Active sessions are held in server memory. Completed game results persist in SQLite.
- The web server binds to `127.0.0.1` by default, so it is intended for local use.
- For public deployment, add authentication, CSRF protection, production hosting, and stronger session management.
- Google Fonts are used for typography when internet access is available; system fallback fonts are provided.
