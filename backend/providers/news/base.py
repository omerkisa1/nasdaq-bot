from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NewsItem:
    headline: str
    summary: str
    source: str
    url: str
    datetime: int  # unix seconds
    external_id: str | None = None


class NewsProvider(ABC):
    @abstractmethod
    async def get_news(self, symbol: str, hours_back: int = 48, limit: int = 10) -> list[NewsItem]:
        ...
