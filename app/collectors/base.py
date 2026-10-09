from dataclasses import dataclass
from typing import Protocol

@dataclass
class Metrics:
    url: str
    platform_id: str | None = None
    creator: str | None = None
    title: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    source: str = "unknown"
    note: str | None = None

class Collector(Protocol):
    name: str
    def fetch(self, url: str) -> Metrics: ...
