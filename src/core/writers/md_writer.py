import re
from pathlib import Path

from src.core.models import GherkinFeature, GherkinStep


def _steps_to_text(steps: list[GherkinStep]) -> str:
    lines = [s.text for s in steps if s.text.strip()]
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    return "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))


def _examples_to_table(examples: list[dict[str, str]]) -> str:
    if not examples:
        return ""
    headers = list(examples[0].keys())
    rows = ["| " + " | ".join(headers) + " |"]
    for row in examples:
        rows.append("| " + " | ".join(row.get(h, "") for h in headers) + " |")
    return "\n".join(rows)


_KNOWN_META_KEYS = {"tags", "test data", "description", "background"}


def _classify_steps(steps: list[GherkinStep]) -> tuple[list[GherkinStep], list[GherkinStep], list[GherkinStep]]:
    given: list[GherkinStep] = []
    when: list[GherkinStep] = []
    then: list[GherkinStep] = []
    section: str | None = None

    for step in steps:
        if step.keyword == "Given":
            section = "given"
            given.append(step)
        elif step.keyword == "When":
            section = "when"
            when.append(step)
        elif step.keyword == "Then":
            section = "then"
            then.append(step)
        elif step.keyword in ("And", "But"):
            if section == "when":
                when.append(step)
            elif section == "then":
                then.append(step)
            else:
                given.append(step)
        else:
            when.append(step)

    if not when and not then:
        given = [s for s in steps if s.keyword == "Given"]
        when = [s for s in steps if s.keyword in ("When", "And", "But")]
        then = [s for s in steps if s.keyword in ("Then", "And", "But") and s not in when]

    return given, when, then


class MarkdownWriter:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def write(self, feature: GherkinFeature) -> None:
        content = self.render(feature)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def render(feature: GherkinFeature) -> str:
        lines: list[str] = []

        lines.append(f"# Module: {feature.name}")

        if feature.tags:
            lines.append(f"**Tags**: {' '.join(feature.tags)}")

        if feature.description:
            lines.append(f"**Description**: {feature.description}")

        for key, val in feature.global_metadata.items():
            if key.lower() not in _KNOWN_META_KEYS:
                lines.append(f"{key}: {val}")

        if feature.background.steps:
            bg_text = _steps_to_text(feature.background.steps)
            if bg_text:
                lines.append("")
                lines.append("**Background**:")
                lines.append(bg_text)

        for scenario in feature.scenarios:
            lines.append("")
            lines.append(f"## Scenario: {scenario.name}")

            for key, val in scenario.local_metadata.items():
                if key.lower() not in _KNOWN_META_KEYS:
                    lines.append(f"**{key}**: {val}")

            if scenario.tags:
                lines.append(f"**Tags**: {' '.join(scenario.tags)}")

            given_steps, when_steps, then_steps = _classify_steps(scenario.steps)

            given_text = _steps_to_text(given_steps) if given_steps else ""
            when_text = _steps_to_text(when_steps) if when_steps else ""
            then_text = _steps_to_text(then_steps) if then_steps else ""

            if feature.background.steps:
                bg_lines = [s.text for s in feature.background.steps if s.text.strip()]
                if given_text:
                    existing = set(line.strip() for line in given_text.split('\n'))
                    for bg_line in bg_lines:
                        stripped_bg = re.sub(r'^\d+\.\s*', '', bg_line).strip()
                        if stripped_bg not in existing:
                            given_text = given_text + "\n" + bg_line
                else:
                    given_text = _steps_to_text(feature.background.steps)

            if given_text:
                lines.append("")
                lines.append("**Precondition**:")
                lines.append(given_text)

            if when_text:
                lines.append("")
                lines.append("**Test Steps**:")
                lines.append(when_text)

            if then_text:
                lines.append("")
                lines.append("**Expected Result**:")
                lines.append(then_text)

            if scenario.examples:
                lines.append("")
                lines.append("**Test Data**:")
                lines.append(_examples_to_table(scenario.examples))
            else:
                td_val = scenario.local_metadata.get("Test Data") or scenario.local_metadata.get("test_data", "")
                if td_val:
                    lines.append("")
                    lines.append(f"**Test Data**: {td_val}")

        lines.append("")
        return "\n".join(lines)
