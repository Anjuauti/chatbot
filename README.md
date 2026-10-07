# Flask Chatbot

A small rule-based chatbot with a REST API, SQLite storage and a simple web UI.

## Structure

```
app.py            Flask app factory + REST routes
chatbot.py        Chatbot logic (no Flask, no database)
models.py         SQLAlchemy models: Conversation, Message
templates/        Chat UI (index.html)
tests/            Chatbot unit tests + API tests
```

## Setup (Python 3.11)

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5000
pytest                           # run tests
```

The database file `chatbot.db` is created automatically in the `instance/` folder.

## API

| Method | Endpoint                               | Purpose                          |
|--------|----------------------------------------|----------------------------------|
| POST   | `/api/conversations`                   | Start a new conversation         |
| GET    | `/api/conversations`                   | List conversations               |
| GET    | `/api/conversations/<id>`              | Get conversation history         |
| POST   | `/api/conversations/<id>/messages`     | Send a message, get the bot reply |

```bash
curl -X POST localhost:5000/api/conversations
curl -X POST localhost:5000/api/conversations/1/messages \
     -H "Content-Type: application/json" -d '{"message": "Hello"}'
curl localhost:5000/api/conversations/1
```

Errors return JSON like `{"error": "Message cannot be empty."}` with status 400
(empty, non-string, missing or over-long message, bad JSON) or 404 (unknown conversation).

## Context memory

The bot reads the earlier messages of the same conversation and uses them:

```
You: My dog's name is Bruno        Bot: Got it. Your dog's name is Bruno.
You: I live in Pune                Bot: Got it. You live in Pune.
You: The meeting is at 5 PM        Bot: Got it, I'll remember that.
You: What is my dog's name?        Bot: Your dog's name is Bruno.
You: When is the meeting?          Bot: You told me earlier: "The meeting is at 5 PM"
You: What do you know about me?    Bot: (lists everything you've told it)
```

Memory is per conversation. A new conversation starts empty.

## Extending the bot

Add a `(regex, reply)` pair to `DEFAULT_RULES` in `chatbot.py`. Rules are checked in order.
To use a smarter engine later, replace `RuleBasedChatbot` with any class that has
`get_response(message, history)`; the API doesn't need to change.
