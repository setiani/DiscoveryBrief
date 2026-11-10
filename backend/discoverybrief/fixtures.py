"""Scripted synthetic clients for the canonical fixture; never call the network."""

import json

from discoverybrief.fixture import FIXTURES


class FixtureResearch:
    def __init__(self):
        self.sources = json.loads(
            (FIXTURES / "research-fixture.json").read_text(encoding="utf-8")
        )["sources"]

    async def search(self, query, start, end):
        return {
            "results": [
                {
                    "url": s["original_url"],
                    "title": s["title"],
                    "content": s["text"],
                    "published_date": s["published_on"],
                }
                for s in self.sources
            ]
        }

    async def extract(self, urls):
        return {
            "results": [
                {"url": s["original_url"], "raw_content": s["text"]}
                for s in self.sources
                if s["original_url"] in urls
            ],
            "failed_results": [],
        }


class FixtureModel:
    def __init__(self):
        self.responses = json.loads(
            (FIXTURES / "role-outputs.json").read_text(encoding="utf-8")
        )

    async def submit(self, messages, schema, max_tokens):
        role = {
            "ResearchPlan": "planner",
            "AnalystOutput": "analyst",
            "VerifierOutput": "verifier",
            "ComposerOutput": "composer",
            "PremiseAudit": "auditor",
        }[schema["title"]]
        return {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "submit_payload",
                                    "arguments": json.dumps(
                                        self.responses[role], ensure_ascii=False
                                    ),
                                }
                            }
                        ]
                    }
                }
            ]
        }
