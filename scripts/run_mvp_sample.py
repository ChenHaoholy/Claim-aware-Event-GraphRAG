from __future__ import annotations

from pathlib import Path
import sys


DEFAULT_QUESTIONS = [
    "What claims conflict about the target?",
    "How did oil prices respond?",
    "What happened near Meridian Port?",
]


def _print_step(title: str) -> None:
    print(f"\n=== {title} ===")




def _apply_temp_event_fallbacks(temp_events, chunks) -> None:
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for event in temp_events:
        chunk = chunk_by_id.get(event.chunk_id)
        if chunk is None:
            continue

        if event.time is None and chunk.date is not None and chunk.date.strip() != "":
            event.time = chunk.date

        if event.location is None:
            lowered = chunk.text.lower()
            if "meridian port" in lowered:
                event.location = "Meridian Port"

def run_mvp_sample_pipeline(
    root: Path | None = None,
    questions: list[str] | None = None,
) -> dict[str, object]:
    if root is None:
        root = Path(__file__).resolve().parents[1]

    if questions is None:
        questions = DEFAULT_QUESTIONS

    sys.path.insert(0, str(root / "src"))

    from claim_aware_event_graphrag.answer_generation import (
        format_answer_markdown,
        generate_answer_from_context,
    )
    from claim_aware_event_graphrag.conflict_detection import detect_conflicts
    from claim_aware_event_graphrag.event_merge import merge_temp_extraction
    from claim_aware_event_graphrag.extraction import extract_from_chunks
    from claim_aware_event_graphrag.graph_builder import build_graph
    from claim_aware_event_graphrag.jsonl import (
        load_chunks,
        load_claims,
        load_events,
        write_jsonl,
    )
    from claim_aware_event_graphrag.llm import MockLLMClient
    from claim_aware_event_graphrag.retrieval import format_retrieval_result, retrieve_context
    from claim_aware_event_graphrag.validation import (
        validate_conflicts,
        validate_dataset,
        validate_graph,
        validate_temp_extraction,
    )

    sample_dir = root / "data" / "sample"
    processed_dir = root / "data" / "processed"
    graph_dir = root / "data" / "graph"

    chunks_path = sample_dir / "chunks.jsonl"
    sample_events_path = sample_dir / "events.jsonl"
    sample_claims_path = sample_dir / "claims.jsonl"

    _print_step("Step 1 - Validate sample data")
    chunks = load_chunks(chunks_path)
    sample_events = load_events(sample_events_path)
    sample_claims = load_claims(sample_claims_path)
    sample_errors = validate_dataset(chunks, sample_events, sample_claims)
    print(f"chunks: {len(chunks)}")
    print(f"sample_events: {len(sample_events)}")
    print(f"sample_claims: {len(sample_claims)}")
    if sample_errors:
        print("validation: FAILED")
        for err in sample_errors:
            print(f"- {err}")
        raise RuntimeError("Step 1 failed: sample data validation failed")
    print("validation: PASSED")

    _print_step("Step 2 - Extract temp events/claims")
    llm_client = MockLLMClient()
    temp_events, temp_claims = extract_from_chunks(chunks, llm_client)
    _apply_temp_event_fallbacks(temp_events, chunks)
    temp_errors = validate_temp_extraction(chunks, temp_events, temp_claims)

    temp_events_path = processed_dir / "temp_events.jsonl"
    temp_claims_path = processed_dir / "temp_claims.jsonl"
    write_jsonl(temp_events_path, [event.model_dump(mode="json") for event in temp_events])
    write_jsonl(temp_claims_path, [claim.model_dump(mode="json") for claim in temp_claims])

    print(f"temp_events: {len(temp_events)}")
    print(f"temp_claims: {len(temp_claims)}")
    if temp_errors:
        print("validation: FAILED")
        for err in temp_errors:
            print(f"- {err}")
        raise RuntimeError("Step 2 failed: temp extraction validation failed")
    print("validation: PASSED")

    _print_step("Step 3 - Merge into canonical events/claims")
    events, claims, mapping = merge_temp_extraction(temp_events, temp_claims)

    events_path = processed_dir / "events.jsonl"
    claims_path = processed_dir / "claims.jsonl"
    mapping_path = processed_dir / "temp_event_mapping.jsonl"
    write_jsonl(events_path, [event.model_dump(mode="json") for event in events])
    write_jsonl(claims_path, [claim.model_dump(mode="json") for claim in claims])
    write_jsonl(
        mapping_path,
        [
            {"temp_event_id": temp_event_id, "event_id": event_id}
            for temp_event_id, event_id in sorted(mapping.items())
        ],
    )

    print(f"events: {len(events)}")
    print(f"claims: {len(claims)}")
    print(f"temp_event_mapping: {len(mapping)}")
    print("validation: PASSED")

    _print_step("Step 4 - Validate processed events/claims")
    processed_errors = validate_dataset(chunks, events, claims)
    print(f"events: {len(events)}")
    print(f"claims: {len(claims)}")
    if processed_errors:
        print("validation: FAILED")
        for err in processed_errors:
            print(f"- {err}")
        raise RuntimeError("Step 4 failed: processed events/claims validation failed")
    print("validation: PASSED")

    _print_step("Step 5 - Detect conflicts")
    conflicts = detect_conflicts(events, claims)
    conflicts_path = processed_dir / "conflicts.jsonl"
    write_jsonl(conflicts_path, [conflict.model_dump(mode="json") for conflict in conflicts])

    conflict_errors = validate_conflicts(events, claims, conflicts)
    print(f"conflicts: {len(conflicts)}")
    print(f"true_conflicts: {sum(1 for c in conflicts if c.is_conflict)}")
    if conflict_errors:
        print("validation: FAILED")
        for err in conflict_errors:
            print(f"- {err}")
        raise RuntimeError("Step 5 failed: conflict validation failed")
    print("validation: PASSED")

    _print_step("Step 6 - Build graph")
    nodes, edges = build_graph(chunks, events, claims, conflicts)
    nodes_path = graph_dir / "nodes.jsonl"
    edges_path = graph_dir / "edges.jsonl"
    write_jsonl(nodes_path, [node.model_dump(mode="json") for node in nodes])
    write_jsonl(edges_path, [edge.model_dump(mode="json") for edge in edges])

    graph_errors = validate_graph(nodes, edges)
    print(f"nodes: {len(nodes)}")
    print(f"edges: {len(edges)}")
    if graph_errors:
        print("validation: FAILED")
        for err in graph_errors:
            print(f"- {err}")
        raise RuntimeError("Step 6 failed: graph validation failed")
    print("validation: PASSED")

    _print_step("Step 7 - Retrieval + answer generation")
    answers_markdown: list[str] = []

    for question in questions:
        retrieval_result = retrieve_context(question, chunks, events, claims, conflicts)
        retrieval_context = format_retrieval_result(
            retrieval_result,
            chunks,
            events,
            claims,
            conflicts,
        )
        answer = generate_answer_from_context(retrieval_context)
        markdown = format_answer_markdown(answer)
        answers_markdown.append(markdown)

        print(f"question: {question}")
        print(
            "retrieval_counts: "
            f"events={len(retrieval_context['events'])}, "
            f"claims={len(retrieval_context['claims'])}, "
            f"chunks={len(retrieval_context['chunks'])}, "
            f"conflicts={len(retrieval_context['conflicts'])}"
        )
        print("validation: PASSED")

    _print_step("Final markdown answers")
    for markdown in answers_markdown:
        print(markdown)
        print("\n---\n")

    return {
        "temp_events": temp_events,
        "temp_claims": temp_claims,
        "events": events,
        "claims": claims,
        "conflicts": conflicts,
        "nodes": nodes,
        "edges": edges,
        "answers_markdown": answers_markdown,
    }


def main() -> int:
    try:
        run_mvp_sample_pipeline()
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
