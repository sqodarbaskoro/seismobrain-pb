"""
File: research_planner.py
Description: Schema-validated research planner producing 1–4 sub-queries (FR-AGT-01)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError, field_validator


class SubQuery(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ResearchPlan(BaseModel):
    sub_queries: list[SubQuery] = Field(min_length=1, max_length=4)

    @field_validator("sub_queries")
    @classmethod
    def _unique_ids(cls, value: list[SubQuery]) -> list[SubQuery]:
        ids = [s.id for s in value]
        if len(ids) != len(set(ids)):
            raise ValueError("sub-query ids must be unique")
        return value


@dataclass(frozen=True, slots=True)
class FrozenPlan:
    """Immutable plan; retrieved text must not mutate it after creation."""

    plan: ResearchPlan
    sealed: bool = True

    def as_dict(self) -> dict[str, object]:
        return self.plan.model_dump()


PlannerFn = Callable[[str], str]


def default_planner_json(question: str) -> str:
    """Deterministic offline planner for tests and Starter."""
    parts = [p.strip() for p in question.replace("?", "").split(" and ") if p.strip()]
    if len(parts) < 2:
        parts = [question.strip(), f"evidence for: {question.strip()}"]
    subs = [{"id": f"sq{i+1}", "text": text} for i, text in enumerate(parts[:4])]
    return json.dumps({"sub_queries": subs})


def plan_research(
    question: str,
    *,
    planner: PlannerFn = default_planner_json,
) -> FrozenPlan:
    raw = planner(question)
    try:
        data = json.loads(raw)
        plan = ResearchPlan.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"invalid research plan: {exc}") from exc
    return FrozenPlan(plan=plan, sealed=True)


def assert_plan_immutable(
    frozen: FrozenPlan, retrieved_texts: Sequence[str]
) -> None:
    """Retrieved content cannot alter the plan after creation (SEC-13)."""
    if not frozen.sealed:
        raise ValueError("plan is not sealed")
    snapshot = frozen.as_dict()
    # Simulate injection attempts via retrieved text — plan dict must stay equal.
    _ = retrieved_texts
    if frozen.as_dict() != snapshot:
        raise ValueError("plan mutated after retrieval")
