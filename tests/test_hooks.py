from app.hooks import analyze_hook

def test_empty_hook_does_not_invent_signals():
    result = analyze_hook(None, None)
    assert result["word_count"] == 0
    assert result["signals"] == []
    assert "impossible" in result["assessment"].lower()

def test_question_and_direct_address():
    result = analyze_hook("Tu savais ça ?")
    assert "question" in result["signals"]
    assert "adresse directe" in result["signals"]

def test_no_virality_claim():
    result = analyze_hook("Dieu peut changer ta vie")
    assert "ne prédit pas la viralité" in result["assessment"]
