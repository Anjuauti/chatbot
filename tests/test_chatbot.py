from chatbot import FALLBACK, RuleBasedChatbot

bot = RuleBasedChatbot()


def test_greeting():
    assert bot.get_response("Hello") == "Hello! How can I help you?"


def test_python_question():
    assert "programming language" in bot.get_response("What is Python?")


def test_goodbye():
    assert bot.get_response("Bye").startswith("Goodbye")


def test_matching_ignores_case_and_punctuation():
    assert bot.get_response("HELLO!!!") == bot.get_response("hello")


def test_unknown_question_uses_fallback():
    assert bot.get_response("What is blorf?") == FALLBACK


def test_remembers_name_from_history():
    history = [{"role": "user", "content": "My name is asha"},
               {"role": "bot", "content": "Nice to meet you, Asha!"}]
    assert "Asha" in bot.get_response("What is my name?", history)


def test_unknown_name_is_handled():
    assert "haven't told me" in bot.get_response("What is my name?", [])


def user(*texts):
    return [{"role": "user", "content": t} for t in texts]


def test_acknowledges_a_fact():
    assert "Bruno" in bot.get_response("My dog's name is Bruno")


def test_recalls_custom_fact():
    history = user("My dog's name is Bruno")
    assert "Bruno" in bot.get_response("What is my dog's name?", history)


def test_recalls_location_age_and_likes():
    history = user("I live in Pune", "I am 25 years old", "I like cricket", "I love music")
    assert "Pune" in bot.get_response("Where do I live?", history)
    assert "25" in bot.get_response("How old am I?", history)
    answer = bot.get_response("What do I like?", history)
    assert "cricket" in answer and "music" in answer


def test_later_fact_overrides_earlier_one():
    history = user("I live in Pune", "I live in Mumbai")
    assert "Mumbai" in bot.get_response("Where do I live?", history)


def test_unknown_fact_is_handled():
    assert "haven't told me" in bot.get_response("What is my favourite colour?", [])


def test_recalls_free_text_context():
    history = user("The meeting is at 5 PM")
    assert "5 PM" in bot.get_response("When is the meeting?", history)


def test_user_context_beats_general_knowledge():
    history = user("Python was created by Guido van Rossum")
    assert "Guido" in bot.get_response("Who created Python?", history)


def test_plain_questions_still_use_knowledge():
    history = user("I like python")
    assert "programming language" in bot.get_response("What is Python?", history)


def test_summary_lists_everything():
    history = user("My name is Asha", "I live in Pune", "Remember that the exam is on Friday")
    answer = bot.get_response("What do you know about me?", history)
    assert "Asha" in answer and "Pune" in answer and "exam is on Friday" in answer


import pytest


@pytest.mark.parametrize("text", ["hi", "hii", "hiii", "helloo", "Hey", "heyy", "HELLO!!"])
def test_greeting_variants(text):
    assert bot.get_response(text) == "Hello! How can I help you?"


@pytest.mark.parametrize("text", ["bye", "byee", "Goodbye", "good night"])
def test_goodbye_variants(text):
    assert bot.get_response(text).startswith("Goodbye")


@pytest.mark.parametrize("text", ["I live in Pune", "i lived in pune", "I am living in Pune", "I'm staying in Pune"])
def test_location_variants(text):
    assert "Pune" in bot.get_response("Where do I live?", user(text))


def test_words_containing_hi_are_not_greetings():
    assert bot.get_response("this thing") != "Hello! How can I help you?"
