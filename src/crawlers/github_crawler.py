from __future__ import annotations

import urllib.request

from src.crawlers.base import BaseCrawler, CrawledDocument


class GitHubRawCrawler(BaseCrawler):
    """Fetch plain text from a GitHub raw URL."""

    source_type = "github_raw"

    def fetch(self, source: str) -> CrawledDocument:
        """Download raw markdown/text from GitHub."""
        with urllib.request.urlopen(source, timeout=10) as response:
            text = response.read().decode("utf-8", errors="ignore")
        return CrawledDocument(source_url=source, source_type=self.source_type, text=text)
