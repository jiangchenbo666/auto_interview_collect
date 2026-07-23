from __future__ import annotations

from src.crawlers.base import BaseCrawler, CrawledDocument


class NowcoderCrawler(BaseCrawler):
    """Placeholder for Nowcoder.

    牛客经常涉及登录、反爬和内容权限，MVP 先不自动抓取。
    推荐先手动保存为 md/txt，再走 import-file。
    """

    source_type = "nowcoder"

    def fetch(self, source: str) -> CrawledDocument:
        raise NotImplementedError(
            "牛客内容第一版建议手动保存为 md/txt 后导入，避免登录和反爬导致不稳定。"
        )
