from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NewsItem:
    headline: str
    summary: str
    source: str
    url: str
    datetime: int  # unix seconds


class NewsProvider(ABC):
    @abstractmethod
    async def get_news(self, symbol: str, hours_back: int = 48) -> list[NewsItem]:
        ...
