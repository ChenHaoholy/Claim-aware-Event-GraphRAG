from claim_aware_event_graphrag.retrieval import (
    format_retrieval_result,
    normalize_query,
    retrieve_context,
    score_claim,
    score_conflict,
    score_event,
    tokenize_query,
)
from claim_aware_event_graphrag.schemas import Chunk, Claim, Conflict, Event


def _data() -> tuple[list[Chunk], list[Event], list[Claim], list[Conflict]]:
    chunks = [
        Chunk(chunk_id="chunk_001", doc_id="d1", source="s1", date=None, text="Strike near Isfahan damaged facilities."),
        Chunk(chunk_id="chunk_002", doc_id="d2", source="s2", date=None, text="Analysts said oil prices could rise after the strike."),
    ]

    events = [
        Event(
            event_id="E001",
            time="2026-03-04",
            type="military",
            summary="A strike happened near Isfahan.",
            actors=["Iran", "Israel"],
            location="Isfahan",
        ),
        Event(
            event_id="E002",
            time="2026-03-05",
            type="economic",
            summary="Oil market reaction after tensions.",
            actors=["Oil traders"],
            location="Global market",
        ),
    ]

    claims = [
        Claim(
            claim_id="C001",
            event_id="E001",
            claimant="State A",
            text="The strike targeted a military facility.",
            topic="target",
            stance="assert",
            source_chunk_id="chunk_001",
        ),
        Claim(
            claim_id="C002",
            event_id="E001",
            claimant="State B",
            text="The strike hit civilian infrastructure.",
            topic="target",
            stance="deny",
            source_chunk_id="chunk_001",
        ),
        Claim(
            claim_id="C003",
            event_id="E002",
            claimant="Analyst",
            text="Oil prices could rise after the incident.",
            topic="economic_impact",
            stance="report",
            source_chunk_id="chunk_002",
        ),
    ]

    conflicts = [
        Conflict(
            conflict_id="CF001",
            event_id="E001",
            claim_ids=["C001", "C002"],
            topic="target",
            is_conflict=True,
            severity="high",
            explanation="Conflicting claims about military vs civilian target.",
        )
    ]

    return chunks, events, claims, conflicts


def test_normalize_query_works() -> None:
    assert normalize_query("  What, Happened?! ") == "what happened"


def test_tokenize_query_removes_stopwords() -> None:
    tokens = tokenize_query("What is the target of the strike in Isfahan")
    assert "the" not in tokens
    assert "strike" in tokens


def test_score_event_related_higher_than_unrelated() -> None:
    _, events, _, _ = _data()
    q = "What happened near Isfahan strike"
    assert score_event(q, events[0]) > score_event(q, events[1])


def test_score_claim_related_higher_than_unrelated() -> None:
    _, _, claims, _ = _data()
    q = "What was the target military facility"
    assert score_claim(q, claims[0]) > score_claim(q, claims[2])


def test_score_conflict_conflict_query_boosted() -> None:
    _, _, claims, conflicts = _data()
    claims_by_id = {c.claim_id: c for c in claims}
    score = score_conflict("What conflict exists about target?", conflicts[0], claims_by_id)
    assert score > 0


def test_retrieve_context_event_expands_claims() -> None:
    chunks, events, claims, conflicts = _data()
    result = retrieve_context("What happened near Isfahan?", chunks, events, claims, conflicts)
    assert "E001" in result.relevant_event_ids
    assert "C001" in result.relevant_claim_ids


def test_retrieve_context_claim_expands_event_and_chunk() -> None:
    chunks, events, claims, conflicts = _data()
    result = retrieve_context("Who said military facility target?", chunks, events, claims, conflicts)
    assert "C001" in result.relevant_claim_ids
    assert "E001" in result.relevant_event_ids
    assert "chunk_001" in result.relevant_chunk_ids


def test_retrieve_context_conflict_expands_relations() -> None:
    chunks, events, claims, conflicts = _data()
    result = retrieve_context("What claims conflict about the target?", chunks, events, claims, conflicts)
    assert "CF001" in result.relevant_conflict_ids
    assert "C001" in result.relevant_claim_ids and "C002" in result.relevant_claim_ids
    assert "E001" in result.relevant_event_ids
    assert "chunk_001" in result.relevant_chunk_ids


def test_retrieve_context_dedup_stable() -> None:
    chunks, events, claims, conflicts = _data()
    result = retrieve_context("target conflict target conflict", chunks, events, claims, conflicts)
    assert len(result.relevant_claim_ids) == len(set(result.relevant_claim_ids))


def test_format_retrieval_result_expands_ids() -> None:
    chunks, events, claims, conflicts = _data()
    result = retrieve_context("What claims conflict about the target?", chunks, events, claims, conflicts)
    formatted = format_retrieval_result(result, chunks, events, claims, conflicts)

    assert formatted["question"]
    assert isinstance(formatted["events"], list)
    assert isinstance(formatted["claims"], list)
    assert isinstance(formatted["chunks"], list)
    assert isinstance(formatted["conflicts"], list)
    assert "debug_info" in formatted
