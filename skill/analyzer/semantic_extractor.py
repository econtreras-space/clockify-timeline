"""Extracts WorkUnit candidates from a NarrativeInput.

This module documents the extraction contract. In practice, the actual
semantic interpretation is performed by Claude during Stage 2 of the skill.
This module defines the output shape, heuristic helpers, and the prompt
template that Claude uses when invoked as the extractor.

Governed by: docs/prompts/analyzer-contract.md, docs/analyzer/semantic-extraction.md
"""

from __future__ import annotations

from domain.types import NarrativeInput, WorkCategory, WorkUnit

# ---------------------------------------------------------------------------
# Prompt template — injected into the Claude reasoning step in SKILL.md Stage 2
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """
You are the Semantic Extractor stage of a timesheet reconstruction system.

Your job: read the narrative below and return a list of WorkUnit candidates.
Each WorkUnit represents a distinct unit of work described or strongly implied by the narrative.

Rules:
- Extract only what the narrative describes or clearly implies. Do not invent.
- Do not assign times yet — semantic meaning only.
- If a task is vague or overloaded, add an ambiguity marker describing why.
- Estimate relative_weight (0.1–1.0) based on apparent cognitive or effort emphasis in the narrative.
- Map each unit to the closest WorkCategory: {categories}

Output format (JSON array):
[
  {{
    "description": "...",
    "category": "...",
    "relative_weight": 0.0,
    "ambiguity_markers": []
  }}
]

Narrative:
{narrative}

Date: {date}
""".strip()


def build_extraction_prompt(narrative_input: NarrativeInput) -> str:
    """Return the prompt string to send to Claude for semantic extraction."""
    return EXTRACTION_PROMPT.format(
        categories=", ".join(c.value for c in WorkCategory),
        narrative=narrative_input.raw_text,
        date=narrative_input.report_date.isoformat(),
    )


def parse_extraction_response(response: list[dict]) -> list[WorkUnit]:
    """Convert Claude's JSON response into typed WorkUnit objects."""
    units: list[WorkUnit] = []
    for item in response:
        try:
            category = WorkCategory(item.get("category", "other"))
        except ValueError:
            category = WorkCategory.OTHER

        units.append(WorkUnit(
            description=item["description"],
            category=category,
            relative_weight=float(item.get("relative_weight", 1.0)),
            ambiguity_markers=item.get("ambiguity_markers", []),
        ))
    return units
