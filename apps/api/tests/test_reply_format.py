from app.services.ai.reply_format import complete_excerpt

def test_short_reply_unchanged():
    assert complete_excerpt("Arthur reviewed the plan.", 100) == "Arthur reviewed the plan."

def test_long_reply_ends_at_sentence():
    result = complete_excerpt("Preston is a test hypothesis. " + "More information " * 30, 80)
    assert result == "Preston is a test hypothesis.\n[Summary shortened]"
    assert len(result) <= 80
