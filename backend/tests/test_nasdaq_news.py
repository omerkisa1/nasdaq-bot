from providers.news.nasdaq_news import map_row_to_newsitem


def test_maps_relative_url_to_absolute():
    row = {
        "id": 12345,
        "title": "CervoMed Faz 2 sonuçlarını açıkladı",
        "description": "Şirket pozitif sonuçlar bildirdi...",
        "publisher": "GlobeNewswire",
        "url": "/press-release/cervomed-faz-2",
    }
    item = map_row_to_newsitem(row)
    assert item.external_id == "12345"
    assert item.url == "https://www.nasdaq.com/press-release/cervomed-faz-2"
    assert item.headline == row["title"]
    assert item.summary == row["description"]
    assert item.source == "GlobeNewswire"


def test_keeps_absolute_url_unchanged():
    row = {"id": 1, "title": "t", "description": "d", "url": "https://example.com/x"}
    item = map_row_to_newsitem(row)
    assert item.url == "https://example.com/x"


def test_missing_publisher_defaults_to_nasdaq():
    row = {"id": 1, "title": "t", "description": "d", "url": "/x"}
    item = map_row_to_newsitem(row)
    assert item.source == "Nasdaq"
