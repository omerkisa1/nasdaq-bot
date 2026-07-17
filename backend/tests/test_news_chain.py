import pytest

from providers.news.base import NewsItem, NewsProvider
from providers.news.chain import ChainedNewsProvider, dedup_news_items


def make_item(external_id=None, url="", headline="h"):
    return NewsItem(headline=headline, summary="s", source="src", url=url, datetime=0, external_id=external_id)


def test_dedup_by_external_id():
    items = [make_item(external_id="1"), make_item(external_id="1"), make_item(external_id="2")]
    result = dedup_news_items(items)
    assert len(result) == 2


def test_dedup_falls_back_to_url_when_no_id():
    items = [make_item(url="https://x/1"), make_item(url="https://x/1"), make_item(url="https://x/2")]
    result = dedup_news_items(items)
    assert len(result) == 2


class StubProvider(NewsProvider):
    def __init__(self, items=None, raises=False):
        self.items = items or []
        self.raises = raises

    async def get_news(self, symbol, hours_back=48, limit=10):
        if self.raises:
            raise RuntimeError("boom")
        return self.items


@pytest.mark.asyncio
async def test_chain_combines_and_dedups_across_providers():
    primary = StubProvider([make_item(external_id="1"), make_item(external_id="2")])
    secondary = StubProvider([make_item(external_id="2"), make_item(external_id="3")])
    chain = ChainedNewsProvider([primary, secondary])

    result = await chain.get_news("ABCD")
    ids = {i.external_id for i in result}
    assert ids == {"1", "2", "3"}


@pytest.mark.asyncio
async def test_chain_survives_provider_failure():
    failing = StubProvider(raises=True)
    working = StubProvider([make_item(external_id="1")])
    chain = ChainedNewsProvider([failing, working])

    result = await chain.get_news("ABCD")
    assert len(result) == 1
