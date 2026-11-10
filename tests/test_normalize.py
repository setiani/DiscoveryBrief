from discoverybrief.normalize import normalize_sources


def test_extract_results_match_by_url_and_failed_snippets_are_not_extracts():
    results = [
        {"url": "https://a.example/one?utm_source=test", "content": "snippet one"},
        {"url": "https://a.example/two", "content": "snippet two"},
    ]
    extraction = {
        "results": [{"url": "https://a.example/two", "raw_content": "full two"}],
        "failed_results": [{"url": "https://a.example/one", "error": "failed"}],
    }
    sources = normalize_sources(results, extraction, "2026-11-08T03:00:00Z")
    assert sources[0]["extraction_status"] == "failed"
    assert sources[0]["text_origin"] == "search_snippet"
    assert sources[1]["extraction_status"] == "ok"
    assert sources[1]["text"] == "full two"
    assert sources[1]["published_on"] is None
