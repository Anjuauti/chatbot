from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _now():
    return datetime.now(timezone.utc)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False, default="New conversation")
    created_at = db.Column(db.DateTime, nullable=False, default=_now)

    messages = db.relationship(
        "Message", backref="conversation", cascade="all, delete-orphan",
        order_by="Message.id",
    )

    def to_dict(self):
        return {"id": self.id, "title": self.title,
                "created_at": self.created_at.isoformat()}


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False)  # "user" or "bot"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)

    def to_dict(self):
        return {"id": self.id, "role": self.role, "content": self.content,
                "created_at": self.created_at.isoformat()}
