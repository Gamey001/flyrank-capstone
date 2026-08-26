"""Rendering the report."""

from __future__ import annotations


def render(plan: dict, data: dict) -> str:
    lines = [f"# {plan.get('title', 'Report')}", ""]
    for section in plan.get("sections", []):
        name = section["name"]
        lines.append(f"## {name.replace('_', ' ').title()}")
        lines.append(f"*{section.get('question', '')}*")
        lines.append("")
        value = data.get(name)
        if isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
        elif value is None:
            lines.append("_no data returned for this section_")
        else:
            lines.append(f"- {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
