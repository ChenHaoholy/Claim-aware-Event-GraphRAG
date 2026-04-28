from __future__ import annotations

import json
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class MockLLMClient:
    """Keyword-based mock extractor for Step 2 tests and scripts."""

    def complete(self, prompt: str) -> str:
        chunk_text = self._extract_chunk_text(prompt)
        text = chunk_text.lower()

        if (("military facility" in text and "civilian infrastructure" in text)
            or ("military logistics warehouse" in text and "civilian fuel depot" in text)
            or ("military logistics warehouse" in text and "not civilian facilities" in text)):
            result = {
                "temp_events": [
                    {
                        "temp_event_id": "e1",
                        "time": None,
                        "type": "military",
                        "summary": "Reported strike concerning facility type.",
                        "actors": ["Defense spokesperson", "Local authority"],
                        "location": None,
                    }
                ],
                "temp_claims": [
                    {
                        "temp_claim_id": "c1",
                        "temp_event_id": "e1",
                        "claimant": "Defense spokesperson",
                        "text": "The strike targeted a military facility.",
                        "topic": "target",
                        "stance": "assert",
                    },
                    {
                        "temp_claim_id": "c2",
                        "temp_event_id": "e1",
                        "claimant": "Local authority",
                        "text": "The strike hit civilian infrastructure.",
                        "topic": "target",
                        "stance": "deny",
                    },
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        if "oil prices" in text or "premium surcharges" in text or "insurers" in text:
            result = {
                "temp_events": [
                    {
                        "temp_event_id": "e1",
                        "time": None,
                        "type": "economic",
                        "summary": "Market impact after regional incident.",
                        "actors": ["Energy analysts"],
                        "location": None,
                    }
                ],
                "temp_claims": [
                    {
                        "temp_claim_id": "c1",
                        "temp_event_id": "e1",
                        "claimant": "Energy analysts",
                        "text": "Oil prices rose after the incident.",
                        "topic": "economic_impact",
                        "stance": "report",
                    }
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        if "could not be independently verified" in text:
            result = {
                "temp_events": [
                    {
                        "temp_event_id": "e1",
                        "time": None,
                        "type": "other",
                        "summary": "Reported incident pending independent verification.",
                        "actors": ["Monitoring group"],
                        "location": None,
                    }
                ],
                "temp_claims": [
                    {
                        "temp_claim_id": "c1",
                        "temp_event_id": "e1",
                        "claimant": "Monitoring group",
                        "text": "The reported details could not be independently verified.",
                        "topic": "verification",
                        "stance": "uncertain",
                    }
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        return json.dumps({"temp_events": [], "temp_claims": []}, ensure_ascii=False)

    @staticmethod
    def _extract_chunk_text(prompt: str) -> str:
        marker = "Chunk text:\n"
        if marker in prompt:
            return prompt.split(marker, maxsplit=1)[1].strip()
        return prompt
