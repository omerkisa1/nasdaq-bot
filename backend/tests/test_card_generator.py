import pytest

from engine.card_generator import parse_gemini_response


def test_parse_plain_json():
    text = '{"has_setup": true, "card": {"direction": "long"}}'
    result = parse_gemini_response(text)
    assert result["has_setup"] is True


def test_parse_markdown_fenced_json():
    text = '```json\n{"has_setup": false, "skip_reason": "hacim yetersiz"}\n```'
    result = parse_gemini_response(text)
    assert result["has_setup"] is False
    assert result["skip_reason"] == "hacim yetersiz"


def test_parse_json_with_surrounding_text():
    text = 'İşte analiz sonucum:\n{"has_setup": true}\nUmarım yardımcı olur.'
    result = parse_gemini_response(text)
    assert result["has_setup"] is True


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        parse_gemini_response("bu bir json değil")
