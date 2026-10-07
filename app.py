from flask import Flask, jsonify, render_template, request

from chatbot import RuleBasedChatbot
from models import Conversation, Message, db

MAX_MESSAGE_LENGTH = 1000
HISTORY_WINDOW = 100  # how many earlier messages the bot gets to see


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chatbot.db"
    if config:
        app.config.update(config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    bot = RuleBasedChatbot()

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    # ---- Pages ----------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html")

    # ---- API ------------------------------------------------------------
    @app.post("/api/conversations")
    def start_conversation():
        conversation = Conversation()
        db.session.add(conversation)
        db.session.commit()
        return jsonify(conversation.to_dict()), 201

    @app.get("/api/conversations")
    def list_conversations():
        conversations = Conversation.query.order_by(Conversation.id.desc()).all()
        return jsonify([c.to_dict() for c in conversations])

    @app.get("/api/conversations/<int:conversation_id>")
    def get_conversation(conversation_id):
        conversation = db.session.get(Conversation, conversation_id)
        if conversation is None:
            return error("Conversation not found.", 404)
        return jsonify({**conversation.to_dict(),
                        "messages": [m.to_dict() for m in conversation.messages]})

    @app.post("/api/conversations/<int:conversation_id>/messages")
    def send_message(conversation_id):
        conversation = db.session.get(Conversation, conversation_id)
        if conversation is None:
            return error("Conversation not found.", 404)

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error("Request body must be a JSON object.", 400)
        text = data.get("message")
        if not isinstance(text, str):
            return error("'message' is required and must be a string.", 400)
        text = text.strip()
        if not text:
            return error("Message cannot be empty.", 400)
        if len(text) > MAX_MESSAGE_LENGTH:
            return error(f"Message is too long (max {MAX_MESSAGE_LENGTH} characters).", 400)

        # Earlier turns only; the bot gets the new message separately.
        earlier = [{"role": m.role, "content": m.content}
                   for m in conversation.messages[-HISTORY_WINDOW:]]
        reply = bot.get_response(text, earlier)

        if not conversation.messages:
            conversation.title = text[:40]
        user_msg = Message(conversation=conversation, role="user", content=text)
        bot_msg = Message(conversation=conversation, role="bot", content=reply)
        db.session.add_all([user_msg, bot_msg])
        db.session.commit()

        return jsonify({
            "conversation": conversation.to_dict(),
            "user_message": user_msg.to_dict(),
            "bot_message": bot_msg.to_dict(),
        }), 201

    # ---- JSON errors for unknown routes / methods -----------------------
    @app.errorhandler(404)
    def not_found(_):
        return error("Not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(_):
        return error("Method not allowed.", 405)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
