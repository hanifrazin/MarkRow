from pathlib import Path
from typing import Any

from src.core.models import GherkinFeature, GherkinScenario

_EXCLUDED_TAG_KEYS = {"tags", "test data", "description", "background"}


def _resolve_indent_spaces() -> int:
    try:
        from src.core.config import ConfigManager
        return getattr(ConfigManager.get(), "indentation_spaces", 2)
    except Exception:
        return 2


def _metadata_to_tags(local_metadata: dict[str, str]) -> list[str]:
    tags: list[str] = []
    for key, val in local_metadata.items():
        if key.lower() in _EXCLUDED_TAG_KEYS:
            continue
        if not val or not val.strip():
            continue
        for part in val.split(","):
            part = part.strip()
            if not part:
                continue
            tag = f"@{part}" if not part.startswith("@") else part
            tags.append(tag)
    return tags


def _dedup_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(tag)
    return result


def _collect_all_tags(scenario: GherkinScenario) -> list[str]:
    return _dedup_tags(scenario.tags + _metadata_to_tags(scenario.local_metadata))


class GherkinWriter:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def write(self, feature: GherkinFeature) -> None:
        indent = _resolve_indent_spaces()
        content = self.render(feature, indent)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def render(feature: GherkinFeature, indent_spaces: int = 2) -> str:
        s = " " * indent_spaces
        lines: list[str] = []

        for tag in feature.tags:
            lines.append(tag)
        if feature.tags:
            lines.append("")

        lines.append(f"Feature: {feature.name}")

        if feature.description:
            for desc_line in feature.description.split("\n"):
                lines.append(f"{s}{desc_line.strip()}")

        for key, val in feature.global_metadata.items():
            if key.lower() not in _EXCLUDED_TAG_KEYS:
                lines.append(f"{s}{key}: {val}")

        if feature.background.steps:
            lines.append("")
            lines.append(f"{s}Background:")
            for step in feature.background.steps:
                lines.append(f"{s * 2}{step.keyword} {step.text}")

        for scenario in feature.scenarios:
            lines.append("")
            all_tags = _collect_all_tags(scenario)
            for tag in all_tags:
                lines.append(f"{s}{tag}")

            if scenario.examples:
                lines.append(f"{s}Scenario Outline: {scenario.name}")
            else:
                lines.append(f"{s}Scenario: {scenario.name}")

            if feature.background.steps and not _has_given_steps(scenario):
                for step in feature.background.steps:
                    lines.append(f"{s * 2}{step.keyword} {step.text}")

            for step in scenario.steps:
                lines.append(f"{s * 2}{step.keyword} {step.text}")

            if scenario.examples:
                lines.append("")
                lines.append(f"{s * 2}Examples:")
                headers = list(scenario.examples[0].keys())
                lines.append(f"{s * 3}| " + " | ".join(headers) + " |")
                for row in scenario.examples:
                    lines.append(f"{s * 3}| " + " | ".join(row.get(h, "") for h in headers) + " |")

        lines.append("")
        return "\n".join(lines)


def _has_given_steps(scenario: GherkinScenario) -> bool:
    return any(s.keyword == "Given" for s in scenario.steps)
