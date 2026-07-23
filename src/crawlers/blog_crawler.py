from __future__ import annotations

import re
import urllib.request

from src.crawlers.base import BaseCrawler, CrawledDocument


class BlogCrawler(BaseCrawler):
    """Very small HTML-to-text crawler for public blog pages."""

    source_type = "blog"

    def fetch(self, source: str) -> CrawledDocument:
        """Fetch a blog URL and strip basic HTML tags."""
        with urllib.request.urlopen(source, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", "\n", text)
        return CrawledDocument(source_url=source, source_type=self.source_type, text=text)
