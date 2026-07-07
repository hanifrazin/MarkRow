from pathlib import Path

from src.core.models import GherkinFeature
from src.core.parsers.gherkin_parser import GherkinParser
from src.core.parsers.md_parser import MarkdownParser as MdParser
from src.core.writers.md_writer import MarkdownWriter
from src.core.writers.gherkin_writer import GherkinWriter
from src.core.writers.excel_writer import ExcelWriter


def convert_file(input_path: str, output_format: str, output_path: str | None = None) -> str:
    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    fmt = output_format.lower()

    if fmt == "md":
        if in_path.suffix not in (".feature", ".featuretext"):
            raise ValueError(f"Input must be a .feature file to convert to Markdown, got: {in_path.suffix}")
        feature = GherkinParser(in_path).parse()
        out_path = Path(output_path) if output_path else in_path.with_suffix(".md")
        MarkdownWriter(out_path).write(feature)
        return str(out_path)

    elif fmt in ("gherkin", "feature"):
        if in_path.suffix != ".md":
            raise ValueError(f"Input must be a .md file to convert to Gherkin, got: {in_path.suffix}")
        feature = MdParser(in_path).parse()
        out_path = Path(output_path) if output_path else in_path.with_suffix(".feature")
        GherkinWriter(out_path).write(feature)
        return str(out_path)

    elif fmt == "excel":
        feature = MdParser(in_path).parse()
        out_path = Path(output_path) if output_path else in_path.with_suffix(".xlsx")
        ExcelWriter(out_path).write(feature, out_path.name)
        return str(out_path)

    else:
        raise ValueError(f"Unsupported output format: {output_format}. Use: md, gherkin, feature, or excel")
