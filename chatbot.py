"""Rule-based chatbot logic.

This module knows nothing about Flask or the database. It takes a message
(plus the earlier turns of the conversation) and returns a reply string, so it
can be unit-tested on its own and later swapped for a smarter engine.

Context handling
----------------
Whatever the user tells the bot is kept in the conversation history, and the
bot uses it in three ways:
  1. Facts      "My dog's name is Bruno", "I live in Pune", "I am 25 years old",
                "I like cricket"  ->  answered later by "What is my dog's name?",
                "Where do I live?", "How old am I?", "What do I like?"
  2. Notes      "Remember that the meeting is at 5 PM" or any plain statement
                ->  found again when a later question shares its key words.
  3. Summary    "What do you know about me?" lists everything learned.
"""
import re
from datetime import datetime

# --- Small-talk rules (also used for short statements) ----------------------
SMALL_TALK_RULES = [
    (r"\b(by+e+|goodbye|see you|farewell|good ?night)\b", "Goodbye! Have a great day."),
    (r"\b(thanks?|thank ?you|thx|ty)\b", "You're welcome! Anything else?"),
    (r"\bhow are you\b", "I'm doing well, thanks for asking. How about you?"),
    (r"\b(h+i+e*|he+y+|he+l+o+|hola|namaste|good (morning|afternoon|evening))\b",
     "Hello! How can I help you?"),
    (r"\b(help|what can you do)\b",
     "I can chat about Python, Flask, SQL and APIs, and I remember what you tell "
     "me. Try 'My name is Sam' and then 'What is my name?'"),
]

# --- Knowledge rules: first match wins, so order matters --------------------
KNOWLEDGE_RULES = [
    (r"\bpython\b",
     "Python is a programming language known for its simple, readable syntax."),
    (r"\bflask\b",
     "Flask is a lightweight Python web framework for building websites and APIs."),
    (r"\bsqlalchemy\b",
     "SQLAlchemy is a Python toolkit that maps database tables to Python classes."),
    (r"\bsqlite\b",
     "SQLite is a small, file-based database that needs no separate server."),
    (r"\b(rest|api)\b",
     "A REST API lets programs talk to each other over HTTP using URLs and JSON."),
    (r"\bwhat time is it\b|\bwhat(?:'s| is) the (time|date)\b",
     lambda: datetime.now().strftime("It's %H:%M on %A, %d %B %Y.")),
    (r"\b(who are you|your name)\b",
     "I'm a small rule-based chatbot built with Flask."),
]

DEFAULT_RULES = SMALL_TALK_RULES + KNOWLEDGE_RULES  # kept for backwards compatibility
FALLBACK = "Sorry, I don't know about that yet. Try asking about Python or Flask."
STATEMENT_ACK = "Got it, I'll remember that."

# --- Patterns for learning facts --------------------------------------------
_END = r"(?=\s+(?:and|but)\s+|[.!?,;\n]|$)"
_VALUE = r"([^.!?,;\n]+?)" + _END

MY_IS = re.compile(r"\bmy ([a-z][a-z' ]{0,30}?) (?:is|are|was) " + _VALUE, re.I)
LIVE = re.compile(r"\bi(?:'m| am)? (?:live|lived|living|stay|stayed|staying) in " + _VALUE, re.I)
FROM = re.compile(r"\bi(?:'m| am) from " + _VALUE, re.I)
AGE = re.compile(r"\bi(?:'m| am) (\d{1,3}) years? old\b", re.I)
LIKE = re.compile(r"\bi (?:really )?(?:like|love|enjoy) ([^.!?;\n]+?)(?=[.!?;\n]|$)", re.I)
NOTE = re.compile(r"^\s*remember (?:that )?(.+?)\s*$", re.I)

# --- Patterns for recalling them --------------------------------------------
RECALL_MY = re.compile(
    r"^\s*(?:what(?:'s| is| are)|tell me|(?:do|can) you (?:know|remember|tell me)) "
    r"my (.+?)\s*[?.!]*\s*$", re.I)
RECALL_OTHER = [
    (re.compile(r"^\s*who am i\b", re.I), "name"),
    (re.compile(r"^\s*where do i (?:live|stay)\b|^\s*where am i (?:from|living)\b", re.I), "location"),
    (re.compile(r"^\s*how old am i\b", re.I), "age"),
    (re.compile(r"^\s*what do i (?:like|love|enjoy)\b", re.I), "likes"),
]
SUMMARY = re.compile(
    r"\b(what did i (?:tell|say)|what do you (?:know|remember)(?: about me)?|"
    r"what have i told)\b", re.I)

QUESTION_START = re.compile(
    r"^\s*(what|who|whom|whose|when|where|why|how|which|is|are|am|do|does|did|"
    r"can|could|will|would|should|tell me)\b", re.I)

STOPWORDS = {
    "what", "who", "whom", "whose", "when", "where", "why", "how", "which", "is",
    "are", "was", "were", "am", "do", "does", "did", "the", "an", "of", "in", "on",
    "at", "to", "for", "my", "me", "you", "your", "it", "and", "or", "tell", "about",
    "can", "could", "will", "would", "should", "have", "has", "had", "that", "this",
    "with", "from", "by", "be", "been", "there", "any", "some",
}


# --- Helpers ----------------------------------------------------------------
def _is_question(text: str) -> bool:
    return text.strip().endswith("?") or bool(QUESTION_START.match(text))


def _norm_key(key: str) -> str:
    key = " ".join(key.lower().split())
    return key.replace("favourite", "favorite").replace("colour", "color")


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _words(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9']+", text.lower())
            if len(w) > 1 and w not in STOPWORDS}


def extract_facts(texts: list[str]) -> dict[str, str]:
    """Collect facts from user statements. Later statements override earlier ones."""
    facts: dict[str, str] = {}
    for text in texts:
        if _is_question(text):
            continue
        for m in MY_IS.finditer(text):
            facts[_norm_key(m.group(1))] = m.group(2).strip()
        for rx in (LIVE, FROM):
            for m in rx.finditer(text):
                facts["location"] = m.group(1).strip()
        for m in AGE.finditer(text):
            facts["age"] = m.group(1)
        for m in LIKE.finditer(text):
            item = m.group(1).strip()
            likes = [x for x in facts.get("likes", "").split(", ") if x]
            if item.lower() not in (x.lower() for x in likes):
                likes.append(item)
            facts["likes"] = ", ".join(likes)
    for key in ("name", "location"):  # "ravi" -> "Ravi", "pune" -> "Pune"
        if key in facts:
            facts[key] = facts[key].title()
    return facts


def describe(key: str, value: str) -> str:
    if key == "location":
        return f"You live in {value}"
    if key == "age":
        return f"You are {value} years old"
    if key == "likes":
        return f"You like {value}"
    return f"Your {key} is {value}"


# --- The bot ----------------------------------------------------------------
class RuleBasedChatbot:
    def __init__(self, small_talk_rules=None, knowledge_rules=None):
        compile_ = lambda rules: [(re.compile(p, re.I), r) for p, r in rules]
        self.small_talk = compile_(SMALL_TALK_RULES if small_talk_rules is None else small_talk_rules)
        self.knowledge = compile_(KNOWLEDGE_RULES if knowledge_rules is None else knowledge_rules)

    def get_response(self, message: str, history: list[dict] | None = None) -> str:
        """Return a reply for `message`.

        `history` is a list of {"role": "user"|"bot", "content": str} dicts
        for the earlier turns of the same conversation.
        """
        text = (message or "").strip()
        user_turns = [t.get("content", "") for t in (history or []) if t.get("role") == "user"]
        facts = extract_facts(user_turns)

        # 1. Questions about things the user told us.
        recalled = self._recall(text, facts, user_turns)
        if recalled:
            return recalled

        question = _is_question(text)

        # 2. New facts in this message ("My dog's name is Bruno").
        if not question:
            new_facts = extract_facts([text])
            if new_facts:
                return self._acknowledge(new_facts)

        # 3. Greetings, thanks, goodbye, help.
        reply = self._match(self.small_talk, text)
        if reply:
            return reply

        if question:
            # 4. Context the user gave beats general knowledge when it fits well.
            turn, score = self._search_context(text, user_turns)
            if turn and score >= 2:
                return self._quote(turn)
            reply = self._match(self.knowledge, text)
            if reply:
                return reply
            return self._quote(turn) if turn else FALLBACK

        # Statements: short ones ("python") still get a knowledge answer;
        # longer ones are treated as context to remember.
        if len(text.split()) <= 3:
            reply = self._match(self.knowledge, text)
            if reply:
                return reply
        return STATEMENT_ACK

    # -- internals -----------------------------------------------------------
    @staticmethod
    def _match(rules, text):
        for pattern, reply in rules:
            if pattern.search(text):
                return reply() if callable(reply) else reply
        return None

    @staticmethod
    def _acknowledge(new_facts: dict[str, str]) -> str:
        if list(new_facts) == ["name"]:
            return f"Nice to meet you, {new_facts['name']}! How can I help?"
        return "Got it. " + ". ".join(describe(k, v) for k, v in new_facts.items()) + "."

    @staticmethod
    def _quote(turn: str) -> str:
        note = NOTE.match(turn)
        return f'You told me earlier: "{(note.group(1) if note else turn).strip()}"'

    @staticmethod
    def _search_context(question: str, user_turns: list[str]):
        """Find the earlier statement sharing the most key words with the question."""
        wanted = _words(question)
        best, best_score = None, 0
        for turn in user_turns:
            if _is_question(turn):
                continue
            score = len(wanted & _words(turn))
            if score and score >= best_score:  # later statements win ties
                best, best_score = turn, score
        return best, best_score

    @staticmethod
    def _recall(text: str, facts: dict[str, str], user_turns: list[str]) -> str | None:
        key = None
        match = RECALL_MY.match(text)
        if match:
            key = _norm_key(match.group(1))
        else:
            for pattern, fixed_key in RECALL_OTHER:
                if pattern.match(text):
                    key = fixed_key
                    break
        if key:
            if key in facts:
                return describe(key, facts[key]) + "."
            return f"You haven't told me your {key} yet."

        if SUMMARY.search(text):
            lines = [describe(k, v) for k, v in facts.items()]
            for turn in user_turns:
                note = NOTE.match(turn)
                if note:
                    lines.append(note.group(1))
            if not lines:
                return "You haven't told me anything yet."
            return "Here's what you've told me:\n" + "\n".join(f"• {line}" for line in lines)
        return None
