import re
from pathlib import Path

from src.core.models import GherkinFeature, GherkinScenario, GherkinStep, GherkinBackground
from src.engine.parser import MarkdownParser as LegacyMarkdownParser


def _parse_steps_text(text: str) -> list[str]:
    if not text:
        return []
    lines = text.strip().split('\n')
    result: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r'^\d+\.\s*', '', line)
        cleaned = re.sub(r'^[-•]\s', '', cleaned)
        cleaned = re.sub(r'^\*\s', '', cleaned)
        result.append(cleaned)
    return result


_PIPE_TABLE_RE = re.compile(r'^\|.+\|$')


def _extract_table_from_lines(lines: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    cleaned: list[str] = []
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        if re.search(r'\**Test Data\**\s*:', line, re.IGNORECASE):
            in_table = True
            continue
        if in_table and _PIPE_TABLE_RE.match(line.strip()):
            table_lines.append(line.strip())
            continue
        if in_table:
            in_table = False
        cleaned.append(line)

    examples: list[dict[str, str]] = []
    if len(table_lines) >= 2:
        headers = [h.strip() for h in table_lines[0].strip('|').split('|')]
        for row in table_lines[1:]:
            cells = [c.strip() for c in row.strip('|').split('|')]
            if len(cells) == len(headers):
                examples.append(dict(zip(headers, cells)))

    return cleaned, examples


class MarkdownParser:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def parse(self) -> GherkinFeature:
        legacy = LegacyMarkdownParser(self.filepath)
        module = legacy.parse()

        raw_content = self.filepath.read_text(encoding='utf-8') if self.filepath.exists() else ""

        feature = GherkinFeature(name=module.name)
        feature.global_metadata = dict(module.global_metadata)

        tags_match = re.search(r'^\*{0,2}Tags\*{0,2}\s*:\s*(.+)$', raw_content, re.MULTILINE | re.IGNORECASE)
        if tags_match:
            feature.tags = [t.strip() for t in tags_match.group(1).split() if t.strip()]
        if not feature.tags:
            for key, val in module.global_metadata.items():
                if key.lower() == "tags":
                    feature.tags = [t.strip() for t in val.split() if t.strip()]

        desc_match = re.search(r'^\*{0,2}Description\*{0,2}\s*:\s*(.+)$', raw_content, re.MULTILINE | re.IGNORECASE)
        if desc_match:
            feature.description = desc_match.group(1).strip()
        if not feature.description:
            for key, val in module.global_metadata.items():
                if key.lower() == "description":
                    feature.description = val

        for sc in module.scenarios:
            scenario = GherkinScenario(name=sc.name)
            scenario.local_metadata = dict(sc.local_metadata)

            tags_val = scenario.local_metadata.pop("Tags", None) or scenario.local_metadata.pop("tags", "")
            if tags_val:
                scenario.tags = [t.strip() for t in tags_val.split() if t.strip()]

            given_lines = _parse_steps_text(sc.precondition)
            when_lines = _parse_steps_text(sc.test_steps)
            then_lines, table_examples = _extract_table_from_lines(_parse_steps_text(sc.expected_result))

            for i, line in enumerate(given_lines):
                kw = "Given" if i == 0 else "And"
                scenario.steps.append(GherkinStep(keyword=kw, text=line))

            for i, line in enumerate(when_lines):
                kw = "When" if i == 0 else "And"
                scenario.steps.append(GherkinStep(keyword=kw, text=line))

            for i, line in enumerate(then_lines):
                kw = "Then" if i == 0 else "And"
                scenario.steps.append(GherkinStep(keyword=kw, text=line))

            scenario.examples = table_examples

            feature.scenarios.append(scenario)

        return feature


def parse_text(content: str) -> GherkinFeature:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        tmp_path = f.name
    try:
        parser = MarkdownParser(tmp_path)
        return parser.parse()
    finally:
        Path(tmp_path).unlink(missing_ok=True)
