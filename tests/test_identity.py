from discoverybrief.identity import domain_matches, resolve_identity


def test_domain_matching_does_not_match_suffix_attack():
    assert domain_matches("news.sagara.example", "sagara.example")
    assert not domain_matches("notsagara.example", "sagara.example")


def test_invented_sources_and_ambiguity_abstain():
    sources = {
        "s1": {"original_url": "https://sagara.example/news"},
        "s2": {"original_url": "https://sagara-logistics.example/news"},
    }
    decision = {
        "status": "matched",
        "domain": "sagara.example",
        "basis_source_ids": ["s1"],
        "candidate_companies": [
            {
                "name": "Sagara Insurance",
                "domain": "sagara.example",
                "source_ids": ["s1"],
            },
            {
                "name": "Sagara Logistics",
                "domain": "sagara-logistics.example",
                "source_ids": ["s2"],
            },
        ],
    }
    assert resolve_identity(None, decision, sources)["status"] == "needs_input"
    assert (
        resolve_identity("sagara.example", decision, sources)["status"] == "user_scoped"
    )
    assert (
        resolve_identity(
            "sagara.example", {**decision, "status": "needs_input"}, sources
        )["status"]
        == "needs_input"
    )
    decision["candidate_companies"] = []
    decision["basis_source_ids"] = ["invented"]
    assert resolve_identity(None, decision, sources)["status"] == "needs_input"


def test_source_backed_analyst_alternative_is_not_lost_by_verifier():
    sources = {
        "s1": {"original_url": "https://news.sagara.example/a"},
        "s2": {"original_url": "https://sagara-logistics.example/b"},
    }
    matched = {
        "name": "Sagara Insurance",
        "domain": "sagara.example",
        "source_ids": ["s1"],
    }
    alternative = {
        "name": "Sagara Logistics",
        "domain": "sagara-logistics.example",
        "source_ids": ["s2"],
    }
    decision = {
        "status": "matched",
        "domain": "sagara.example",
        "basis_source_ids": ["s1"],
        "candidate_companies": [matched],
    }
    assert (
        resolve_identity(None, decision, sources, [alternative])["status"]
        == "needs_input"
    )
    alternative["source_ids"] = ["invented"]
    assert (
        resolve_identity(None, decision, sources, [alternative])["status"] == "matched"
    )
