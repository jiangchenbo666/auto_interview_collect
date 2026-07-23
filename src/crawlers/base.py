from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrawledDocument:
    """Normalized output returned by all crawler implementations."""

    source_url: str
    source_type: str
    text: str


class BaseCrawler:
    """Crawler interface. Subclasses fetch text from one kind of source."""

    source_type = "base"

    def fetch(self, source: str) -> CrawledDocument:
        raise NotImplementedError
