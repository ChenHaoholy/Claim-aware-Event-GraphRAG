from claim_aware_event_graphrag.prompts import build_event_claim_extraction_prompt
from claim_aware_event_graphrag.schemas import Chunk


def _chunk() -> Chunk:
    return Chunk(
        chunk_id="chunk_001",
        doc_id="doc_1",
        source="sample",
        date="2026-03-04",
        text="Officials said the strike targeted a military warehouse, not civilian facilities.",
    )


def test_prompt_mentions_multi_claim_extraction_requirement() -> None:
    prompt = build_event_claim_extraction_prompt(_chunk())

    assert "如果一句话包含多个 claim，必须拆开为多条 claim" in prompt
    assert "military warehouse was targeted" in prompt
    assert "civilian facilities were not targeted" in prompt


def test_prompt_mentions_economic_impact_mapping() -> None:
    prompt = build_event_claim_extraction_prompt(_chunk())

    assert "economic impact 相关说法统一归入 topic=economic_impact" in prompt
    assert "oil prices rose" in prompt
    assert "insurance premiums increased" in prompt
    assert "port operations slowed" in prompt
    assert "shipping costs increased" in prompt


def test_prompt_mentions_verification_uncertain_mapping() -> None:
    prompt = build_event_claim_extraction_prompt(_chunk())

    assert "topic=verification, stance=uncertain" in prompt
    assert "not independently confirmed" in prompt
