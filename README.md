# Flask Chatbot

A small rule-based chatbot with a REST API, SQLite storage and a simple web UI.


## Setup (Python 3.11)

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5000
pytest                           # run tests
```

The database file `chatbot.db` is created automatically in the `instance/` folder.



