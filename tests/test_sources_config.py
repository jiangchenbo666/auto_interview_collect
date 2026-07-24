from __future__ import annotations

from src.main import load_public_sources


def test_load_public_sources_reads_enabled_urls(tmp_path):
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: enabled source
    type: public_url
    enabled: true
    url: https://example.com/a
  - name: disabled source
    type: public_url
    enabled: false
    url: https://example.com/b
""",
        encoding="utf-8",
    )

    sources = load_public_sources(config)

    assert len(sources) == 1
    assert sources[0]["url"] == "https://example.com/a"


def test_load_public_sources_reads_default_config():
    sources = load_public_sources("config/real_sources.yaml")

    assert sources
    assert all(source["type"] == "public_url" for source in sources)
