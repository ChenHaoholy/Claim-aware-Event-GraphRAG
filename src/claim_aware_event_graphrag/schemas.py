from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


EventType = Literal[
    "military",
    "diplomatic",
    "economic",
    "maritime",
    "nuclear",
    "humanitarian",
    "political",
    "other",
]

ClaimTopic = Literal[
    "responsibility",
    "target",
    "casualty",
    "damage",
    "economic_impact",
    "policy",
    "verification",
    "cause",
    "response",
    "other",
]

ClaimStance = Literal["assert", "deny", "uncertain", "report"]
ConflictSeverity = Literal["low", "medium", "high", "none"]

GraphNodeType = Literal["event", "claim", "chunk", "actor", "location", "conflict"]
GraphEdgeType = Literal[
    "ABOUT",
    "SUPPORTED_BY",
    "MADE_BY",
    "INVOLVES_ACTOR",
    "OCCURRED_AT",
    "HAS_CONFLICT",
    "CONFLICTS_WITH",
]


class Chunk(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    chunk_id: str
    doc_id: str
    source: str | None = None
    date: str | None = None
    text: str

    @field_validator("chunk_id", "doc_id", "text")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value


class Event(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str
    time: str | None = None
    type: EventType
    summary: str
    actors: list[str]
    location: str | None = None

    @field_validator("event_id", "summary")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @field_validator("actors")
    @classmethod
    def actors_cannot_contain_empty_strings(cls, value: list[str]) -> list[str]:
        for actor in value:
            if actor.strip() == "":
                raise ValueError("actors must not contain empty strings")
        return value


class Claim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    claim_id: str
    event_id: str
    claimant: str
    text: str
    topic: ClaimTopic
    stance: ClaimStance
    source_chunk_id: str

    @field_validator("claim_id", "event_id", "claimant", "text", "source_chunk_id")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value


class TempEvent(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_event_id: str
    chunk_id: str
    time: str | None = None
    type: EventType
    summary: str
    actors: list[str]
    location: str | None = None

    @field_validator("temp_event_id", "chunk_id", "summary")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @field_validator("actors")
    @classmethod
    def actors_cannot_contain_empty_strings(cls, value: list[str]) -> list[str]:
        for actor in value:
            if actor.strip() == "":
                raise ValueError("actors must not contain empty strings")
        return value


class TempClaim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_claim_id: str
    temp_event_id: str
    chunk_id: str
    claimant: str
    text: str
    topic: ClaimTopic
    stance: ClaimStance
    source_chunk_id: str

    @field_validator(
        "temp_claim_id",
        "temp_event_id",
        "chunk_id",
        "claimant",
        "text",
        "source_chunk_id",
    )
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def source_chunk_should_match_chunk(self) -> "TempClaim":
        if self.source_chunk_id != self.chunk_id:
            raise ValueError("source_chunk_id must equal chunk_id for TempClaim")
        return self


class ExtractionResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_events: list[TempEvent]
    temp_claims: list[TempClaim]

    @model_validator(mode="after")
    def claims_must_reference_existing_temp_events(self) -> "ExtractionResult":
        event_ids = {event.temp_event_id for event in self.temp_events}
        for claim in self.temp_claims:
            if claim.temp_event_id not in event_ids:
                raise ValueError(
                    f"TempClaim {claim.temp_claim_id} references missing temp_event_id {claim.temp_event_id}"
                )
        return self


class Conflict(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    conflict_id: str
    event_id: str
    claim_ids: list[str]
    topic: ClaimTopic
    is_conflict: bool
    severity: ConflictSeverity
    explanation: str

    @field_validator("conflict_id", "event_id", "explanation")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @field_validator("claim_ids")
    @classmethod
    def claim_ids_must_have_multiple_items(cls, value: list[str]) -> list[str]:
        if len(value) < 2:
            raise ValueError("claim_ids must contain at least 2 claim ids")
        for claim_id in value:
            if claim_id.strip() == "":
                raise ValueError("claim_ids must not contain empty claim_id")
        return value

    @model_validator(mode="after")
    def severity_must_match_conflict_flag(self) -> "Conflict":
        if not self.is_conflict and self.severity != "none":
            raise ValueError("severity must be 'none' when is_conflict is false")
        if self.is_conflict and self.severity == "none":
            raise ValueError("severity must not be 'none' when is_conflict is true")
        return self



class GraphNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    node_id: str
    node_type: GraphNodeType
    label: str
    properties: dict[str, object]

    @field_validator("node_id", "label")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value


class GraphEdge(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    edge_id: str
    source_id: str
    target_id: str
    edge_type: GraphEdgeType
    properties: dict[str, object]

    @field_validator("edge_id", "source_id", "target_id")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value



class RetrievalResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str
    relevant_event_ids: list[str]
    relevant_claim_ids: list[str]
    relevant_chunk_ids: list[str]
    relevant_conflict_ids: list[str]
    debug_info: dict[str, object]

    @field_validator("question")
    @classmethod
    def question_must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("question must not be empty")
        return value



class AnswerResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str
    conclusion: str
    key_events: list[dict[str, object]]
    claims_by_actor: dict[str, list[dict[str, object]]]
    conflicts_and_uncertainty: list[dict[str, object]]
    evidence: list[dict[str, object]]
    limitations: list[str]

    @field_validator("question", "conclusion")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value
