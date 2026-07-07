from pathlib import Path

from src.core.models import GherkinFeature
from src.engine.exporter import ExcelExporter as LegacyExcelExporter
from src.models.testcase import Module, Scenario


class ExcelWriter:
    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self._legacy = LegacyExcelExporter(self.output_path.parent if self.output_path.suffix else self.output_path)

    def write(self, feature: GherkinFeature, output_filename: str | None = None) -> None:
        module = self._feature_to_module(feature)
        filename = output_filename or f"{feature.name}.xlsx"
        self._legacy.export(module, filename)

    @staticmethod
    def _feature_to_module(feature: GherkinFeature) -> Module:
        module = Module(name=feature.name)
        module.global_metadata = dict(feature.global_metadata)
        if feature.tags:
            module.global_metadata["Tags"] = " ".join(feature.tags)
        if feature.description:
            module.global_metadata["Description"] = feature.description

        for scenario in feature.scenarios:
            sc = Scenario(name=scenario.name)
            sc.local_metadata = dict(scenario.local_metadata)
            if scenario.tags:
                sc.local_metadata["Tags"] = " ".join(scenario.tags)

            for step in scenario.steps:
                if step.keyword in ("Given", "And"):
                    if any(s.keyword in ("When", "Then") for s in scenario.steps):
                        sc.precondition += step.text + "\n"
                if step.keyword in ("When", "And"):
                    if any(s.keyword == "When" for s in scenario.steps):
                        sc.test_steps += step.text + "\n"
                if step.keyword in ("Then", "And"):
                    if any(s.keyword == "Then" for s in scenario.steps):
                        sc.expected_result += step.text + "\n"

            if feature.background.steps:
                for step in feature.background.steps:
                    if step.text.strip():
                        sc.precondition = (sc.precondition + step.text + "\n").strip()

            module.scenarios.append(sc)

        return module
