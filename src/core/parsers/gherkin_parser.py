import re
from pathlib import Path

from src.core.models import GherkinFeature, GherkinScenario, GherkinStep, GherkinBackground

_STEP_KEYWORDS = {"Given", "When", "Then", "And", "But"}
_TAG_RE = re.compile(r'@\S+')
_META_RE = re.compile(r'^([A-Za-z][A-Za-z0-9 /_-]*):\s*(.*)$')


class GherkinParseError(ValueError):
    pass


class GherkinParser:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def parse(self) -> GherkinFeature:
        with open(self.filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return self._parse_lines(lines)

    @staticmethod
    def _parse_lines(lines: list[str]) -> GherkinFeature:
        feature: GherkinFeature | None = None
        current_scenario: GherkinScenario | None = None
        background_steps: list[GherkinStep] = []
        in_background = False
        in_examples = False
        examples_headers: list[str] = []
        pending_tags: list[str] = []
        before_first_scenario: list[str] = []

        feature_header_collected = False

        for raw_line in lines:
            line = raw_line.rstrip('\n')
            stripped = line.strip()

            if not stripped:
                in_examples = False
                continue

            if stripped.startswith('#'):
                if current_scenario is not None:
                    meta_match = re.match(r'^#\s*(.+?)\s*:\s*(.+)$', stripped)
                    if meta_match:
                        current_scenario.local_metadata[meta_match.group(1).strip()] = meta_match.group(2).strip()
                in_examples = False
                continue

            tags = _TAG_RE.findall(stripped)
            if tags and not any(stripped.startswith(kw) for kw in ["Feature:", "Scenario:", "Scenario Outline:", "Background:", "Examples:"]):
                pending_tags.extend(tags)
                continue

            if stripped.startswith('@') and tags:
                pending_tags.extend(tags)
                continue

            if stripped.startswith('Feature:'):
                feature = GherkinFeature(name=stripped[len('Feature:'):].strip())
                feature.tags = list(pending_tags)
                pending_tags = []
                in_background = False
                in_examples = False
                continue

            if feature is None:
                continue

            scenario_keywords = ["Scenario:", "Scenario Outline:", "Background:", "Examples:"]

            if in_examples:
                if stripped.startswith('|'):
                    cells = [c.strip() for c in stripped.strip('|').split('|')]
                    if not examples_headers:
                        examples_headers = cells
                    elif current_scenario is not None:
                        if len(cells) == len(examples_headers):
                            current_scenario.examples.append(dict(zip(examples_headers, cells)))
                else:
                    in_examples = False
                continue

            if stripped.startswith('Background:'):
                in_background = True
                current_scenario = None
                in_examples = False
                if not feature_header_collected:
                    _flush_before_first_scenario(feature, before_first_scenario)
                    before_first_scenario = []
                    feature_header_collected = True
                continue

            if stripped.startswith('Scenario Outline:'):
                in_background = False
                in_examples = False
                if not feature_header_collected:
                    _flush_before_first_scenario(feature, before_first_scenario)
                    before_first_scenario = []
                    feature_header_collected = True
                name = stripped[len('Scenario Outline:'):].strip()
                current_scenario = GherkinScenario(name=name, tags=list(pending_tags))
                pending_tags = []
                feature.scenarios.append(current_scenario)
                continue

            if stripped.startswith('Scenario:'):
                in_background = False
                in_examples = False
                if not feature_header_collected:
                    _flush_before_first_scenario(feature, before_first_scenario)
                    before_first_scenario = []
                    feature_header_collected = True
                name = stripped[len('Scenario:'):].strip()
                current_scenario = GherkinScenario(name=name, tags=list(pending_tags))
                pending_tags = []
                feature.scenarios.append(current_scenario)
                continue

            if stripped.startswith('Examples:') or stripped.startswith('Example:'):
                in_examples = True
                examples_headers = []
                continue

            step_kw = stripped.split()[0] if stripped.split() else ""
            step_text = stripped[len(step_kw):].strip() if step_kw in _STEP_KEYWORDS else ""

            if step_kw in _STEP_KEYWORDS and step_text:
                step = GherkinStep(keyword=step_kw, text=step_text)
                if in_background:
                    background_steps.append(step)
                elif current_scenario is not None:
                    current_scenario.steps.append(step)
                continue

            if not feature_header_collected:
                if not any(stripped.startswith(kw) for kw in scenario_keywords + ["@"]):
                    before_first_scenario.append(stripped)

        if feature is None:
            raise GherkinParseError("No Feature: declaration found in file")

        if not feature_header_collected:
            _flush_before_first_scenario(feature, before_first_scenario)

        if background_steps:
            feature.background = GherkinBackground(steps=background_steps)

        if pending_tags:
            feature.tags.extend(pending_tags)

        return feature


def _flush_before_first_scenario(feature: GherkinFeature, lines: list[str]) -> None:
    desc_parts: list[str] = []
    for line in lines:
        meta_match = _META_RE.match(line)
        if meta_match:
            feature.global_metadata[meta_match.group(1).strip()] = meta_match.group(2).strip()
        else:
            desc_parts.append(line)
    if desc_parts:
        feature.description = " ".join(desc_parts)


def parse_text(content: str) -> GherkinFeature:
    lines = content.split('\n')
    return GherkinParser._parse_lines(lines)
