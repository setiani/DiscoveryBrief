"""Local fixed evidence for evaluations; this adapter never calls Tavily or the network."""

import hashlib
from copy import deepcopy
from urllib.parse import urlsplit

from discoverybrief.research import normalize_url


class FrozenResearch:
    def __init__(self, fixture: dict):
        if fixture.get("synthetic") is not True:
            raise ValueError("only synthetic fixed research is supported")
        sources = fixture.get("sources")
        if not isinstance(sources, list) or len(sources) > 10:
            raise ValueError("invalid fixed source list")
        self._sources = []
        seen = set()
        for source in sources:
            url = normalize_url(source["canonical_url"])
            if not (urlsplit(url).hostname or "").endswith(".example") or url in seen:
                raise ValueError("invalid or duplicate synthetic URL")
            content = source["text"]
            if (
                hashlib.sha256(content.encode("utf-8")).hexdigest()
                != source["content_sha256"]
            ):
                raise ValueError("fixed source hash mismatch")
            seen.add(url)
            self._sources.append(deepcopy(source))

    async def search(self, query: dict, start_date: str, end_date: str) -> dict:
        # All systems see the same fixed evidence, independently of model query choices.
        return {
            "results": [
                {
                    "url": source["canonical_url"],
                    "title": source["title"],
                    "content": source["text"],
                    "published_date": source.get("raw_provider_date"),
                }
                for source in self._sources
            ]
        }

    async def extract(self, urls: list[str]) -> dict:
        requested = set(urls)
        results, failed = [], []
        for source in self._sources:
            url = source["canonical_url"]
            if url not in requested:
                continue
            if (
                source.get("extraction_status") == "ok"
                and source.get("text_origin") == "extract"
            ):
                results.append({"url": url, "raw_content": source["text"]})
            else:
                failed.append({"url": url})
        return {"results": results, "failed_results": failed}
