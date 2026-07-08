import argparse
import re
import sys
from pathlib import Path
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

custom_theme = Theme({
    "primary": "bold cyan1",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "bold blue",
    "path": "bright_cyan underline",
    "file": "bright_green",
    "dim": "dim white",
    "accent": "magenta",
    "highlight": "bold yellow on blue",
})

console = Console(theme=custom_theme)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.config import ConfigManager
from src.engine.parser import MarkdownParser
from src.engine.exporter import ExcelExporter
from src.core.utils.config_loader import load_config_with_migration
from src.cli.router import convert_file


def sanitize_folder_name(name: str) -> str:
    """
    Sanitize a folder name for safe filesystem usage.

    - Extracts just the final name component (strips path traversal like ``../``).
    - Replaces illegal OS characters (``< > : " / \\ | ? *`` and null) with ``_``.
    - Strips leading/trailing dots and spaces (Windows restriction).
    - Falls back to ``"default"`` if the result is empty or invalid.
    """
    # Extract just the leaf name — inherently removes any path-traversal prefix
    name = Path(name).name

    # Remove/replace characters illegal in folder names across Windows/Linux/Mac
    sanitized = re.sub(r'[<>:"/\\|?*\x00]', '_', name)

    # Strip leading/trailing dots and spaces (Windows limitation)
    sanitized = sanitized.strip('. ')

    # If empty or a special directory entry, use fallback
    if not sanitized or sanitized in ('.', '..'):
        return 'default'

    return sanitized


def create_result_subfolder(input_path: Path, base_output_dir: Path) -> Path:
    """
    If *input_path* is a **directory**, create a ``result_<sanitized_name>``
    subfolder inside *base_output_dir* and return its path.

    If *input_path* is a **file**, return *base_output_dir* unchanged
    (no subfolder created).

    Edge cases handled:
    - Path traversal and illegal characters via :func:`sanitize_folder_name`.
    - Empty / root directory name (falls back to ``"default"``).
    - File-vs-directory collision (exits with a rich error Panel).
    - Permission and OSError (exits with a rich error Panel).
    """
    if not input_path.is_dir():
        return base_output_dir

    folder_name = sanitize_folder_name(input_path.name)
    result_dir = base_output_dir / f"result_{folder_name}"

    # Collision: exists but is a FILE, not a directory
    if result_dir.exists() and not result_dir.is_dir():
        console.print(Panel(
            f"[error]Cannot create folder '[path]{result_dir}[/path]': "
            f"a file with the same name already exists.[/error]",
            title="[error]Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)

    # Try to create the folder
    try:
        result_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"  [info]Created sub-folder:[/info] [path]{result_dir}/[/path]")
    except PermissionError:
        console.print(Panel(
            f"[error]Permission denied: Cannot create folder "
            f"'[path]{result_dir}[/path]'.[/error]\n"
            f"[warning]Please check your folder permissions and try again.[/warning]",
            title="[error]Permission Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)
    except OSError as e:
        console.print(Panel(
            f"[error]Failed to create folder '[path]{result_dir}[/path]': "
            f"{e}[/error]",
            title="[error]OS Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)

    return result_dir


def print_banner():
    banner = Text()
    banner.append("      __  __    _    __  __  _____        __      \n", style="primary")
    banner.append("     |  \\/  |  / \\  |  \\/  |/ _ \\ \\      / /     \n", style="accent")
    banner.append("     | |\\/| | / _ \\ | |\\/| | | | \\ \\ /\\ / /      \n", style="info")
    banner.append("     | |  | |/ ___ \\| |  | | |_| |\\ V  V /       \n", style="success")
    banner.append("     |_|  |_/_/   \\_\\_|  |_|\\___/  \\_/\\_/        \n", style="warning")
    banner.append("\n")
    banner.append("              ", style="dim")
    banner.append("Markdown", style="bold magenta")
    banner.append(" ", style="dim")
    banner.append("To", style="bold blue")
    banner.append(" ", style="dim")
    banner.append("M", style="bold yellow")
    banner.append("-", style="dim")
    banner.append("Rows", style="bold green")
    console.print(Panel.fit(banner, border_style="primary", padding=(1, 2)))

def print_main_help():
    """Print main help with overview of all commands."""
    console.print()
    console.print(Rule("[primary]MAMOW[/primary] - [dim]Command Overview[/dim]", style="primary"))
    console.print()
    
    console.print("[info]MAMOW[/info] is a multi-format test case converter with three main modes:")
    console.print()
    
    # Command overview table
    table = Table(show_header=True, header_style="primary", border_style="dim", pad_edge=False)
    table.add_column("Command", style="accent", no_wrap=True)
    table.add_column("Description", style="info")
    table.add_column("Quick Example", style="dim")
    
    table.add_row(
        "[primary]mamow[/primary] [info]-i[/info] INPUT",
        "Markdown → Excel conversion (legacy mode)",
        "mamow -i test.md -o output.xlsx"
    )
    table.add_row(
        "[primary]mamow convert[/primary] [info]-i[/info] INPUT [info]-f[/info] FORMAT",
        "Convert between formats (Gherkin ↔ Markdown ↔ Excel)",
        "mamow convert -i test.md -f gherkin"
    )
    
    console.print(table)
    console.print()
    
    # Quick help for each mode
    console.print(Panel(
        "[primary]1. Markdown → Excel (Legacy Mode)[/primary]\n"
        "  For converting Markdown test cases to Excel spreadsheets\n"
        "  [dim]Usage:[/dim] [primary]mamow[/primary] [info]-i[/info] INPUT [info]-o[/info] OUTPUT [info][OPTIONS][/info]\n"
        "  [dim]More help:[/dim] [primary]mamow --help[/primary]\n\n"
        
        "[primary]2. Format Conversion (Convert Mode)[/primary]\n"
        "  For converting between Gherkin, Markdown, and Excel formats\n"
        "  [dim]Usage:[/dim] [primary]mamow convert[/primary] [info]-i[/info] INPUT [info]-f[/info] {md|gherkin|feature|excel} [info]-o[/info] OUTPUT\n"
        "  [dim]More help:[/dim] [primary]mamow convert --help[/primary]\n\n"
        
        "[primary]3. Get Specific Help[/primary]\n"
        "  [dim]•[/dim] [primary]mamow --help[/primary] - Markdown to Excel help\n"
        "  [dim]•[/dim] [primary]mamow convert --help[/primary] - Format conversion help",
        title="[primary]Usage Modes[/primary]",
        border_style="accent",
        expand=False
    ))

def print_md_to_excel_help():
    """Print help for Markdown to Excel conversion."""
    console.print()
    console.print(Rule("[primary]MAMOW[/primary] - [dim]Markdown → Excel Conversion[/dim]", style="primary"))
    console.print()
    
    console.print("[info]Convert Markdown test cases to Excel spreadsheets[/info]")
    console.print()
    
    table = Table(show_header=True, header_style="primary", border_style="dim", pad_edge=False)
    table.add_column("Option", style="accent", no_wrap=True)
    table.add_column("Description", style="info")
    table.add_column("Default", style="dim")
    
    table.add_row("-i, --input", "Path to input Markdown file or directory", "[required]")
    table.add_row("-o, --output", "Path to output file or directory", "config default")
    table.add_row("-c, --config", "Path to config.json", "config.json")
    table.add_row("--merge", "Merge all .md files in directory into 1 .xlsx", "off")
    table.add_row("--single", "Export each .md file to separate .xlsx files", "off")
    table.add_row("-h, --help", "Show this help message and exit", "")
    
    console.print(table)
    console.print()
    
    console.print(Panel(
        "[dim]Examples:[/dim]\n"
        "  [primary]Convert single file[/primary]\n"
        "    mamow -i samples/input/test.md -o output/test.xlsx\n\n"
        "  [primary]Merge directory[/primary]\n"
        "    mamow -i samples/input/ --merge -o output/merged.xlsx\n\n"
        "  [primary]Process directory (individual files)[/primary]\n"
        "    mamow -i samples/input/ -o output/\n\n"
        "  [primary]Single file mode[/primary]\n"
        "    mamow -i samples/input/ --single -o output/",
        title="[primary]Usage Examples[/primary]",
        border_style="accent",
        expand=False
    ))
    
    console.print()
    console.print("[dim]Note:[/dim] Use [primary]mamow convert[/primary] for Gherkin ↔ Markdown conversions")

def print_convert_help():
    """Print help for format conversion."""
    console.print()
    console.print(Rule("[primary]MAMOW[/primary] - [dim]Format Conversion[/dim]", style="primary"))
    console.print()
    
    console.print("[info]Convert between Gherkin, Markdown, and Excel formats[/info]")
    console.print()
    
    table = Table(show_header=True, header_style="primary", border_style="dim", pad_edge=False)
    table.add_column("Option", style="accent", no_wrap=True)
    table.add_column("Description", style="info")
    table.add_column("Default", style="dim")
    
    table.add_row("-i, --input", "Path to input file", "[required]")
    table.add_row("-f, --format", "Target output format: md, gherkin, feature, excel", "[required]")
    table.add_row("-o, --output", "Path to output file (default: auto-generated)", "auto")
    table.add_row("-h, --help", "Show this help message and exit", "")
    
    console.print(table)
    console.print()
    
    # Format conversion matrix
    console.print(Panel(
        "[primary]Supported Conversions:[/primary]\n"
        "  [dim]•[/dim] [info]Markdown → Gherkin[/info]   (md → .feature)\n"
        "  [dim]•[/dim] [info]Gherkin → Markdown[/info]   (.feature → md)\n"
        "  [dim]•[/dim] [info]Markdown → Excel[/info]      (md → .xlsx)\n"
        "  [dim]•[/dim] [info]Gherkin → Excel[/info]       (.feature → .xlsx)\n\n"
        
        "[primary]Format Details:[/primary]\n"
        "  [dim]•[/dim] [info]md[/info]        - Markdown file (.md)\n"
        "  [dim]•[/dim] [info]gherkin[/info]  - Gherkin/Feature file (.feature)\n"
        "  [dim]•[/dim] [info]feature[/info]   - Alias for gherkin\n"
        "  [dim]•[/dim] [info]excel[/info]     - Excel spreadsheet (.xlsx)",
        title="[primary]Conversion Matrix[/primary]",
        border_style="accent",
        expand=False
    ))
    
    console.print()
    console.print(Panel(
        "[dim]Examples:[/dim]\n"
        "  [primary]Markdown → Gherkin[/primary]\n"
        "    mamow convert -i test.md -f gherkin -o test.feature\n\n"
        "  [primary]Gherkin → Markdown[/primary]\n"
        "    mamow convert -i test.feature -f md -o test.md\n\n"
        "  [primary]Markdown → Excel[/primary]\n"
        "    mamow convert -i test.md -f excel -o test.xlsx\n\n"
        "  [primary]Auto output naming[/primary]\n"
        "    mamow convert -i input.feature -f md",
        title="[primary]Usage Examples[/primary]",
        border_style="accent",
        expand=False
    ))

def process_file(input_path: Path, out_dir: Path, out_name: str):
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="primary"),
        TextColumn("[primary]Processing[/primary] [path]{task.description}[/path]"),
        BarColumn(bar_width=None, style="dim", complete_style="primary"),
        TaskProgressColumn(style="info"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(str(input_path.name), total=None)
        try:
            md_parser = MarkdownParser(input_path)
            module = md_parser.parse()
            
            exporter = ExcelExporter(out_dir)
            exporter.export(module, out_name)
            console.print(f"  [success]✓[/success] Exported to [path]{out_dir / out_name}[/path]")
        except Exception as e:
            console.print(f"  [error]✗[/error] [error]Error processing {input_path}: {e}[/error]")

def run_convert(args: argparse.Namespace) -> None:
    try:
        out = convert_file(args.input, args.format, args.output)
        console.print(f"  [success]✓[/success] Converted to [path]{out}[/path]")
    except Exception as e:
        console.print(Panel(
            f"[error]{e}[/error]",
            title="[error]Conversion Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MAMOW: Parse Markdown test cases into Excel",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input Markdown file or directory")
    parser.add_argument("-o", "--output", default=None, help="Path to output file or directory")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config.json")
    parser.add_argument("--merge", action="store_true", help="Merge all .md files in directory into 1 .xlsx file")
    parser.add_argument("--single", dest="single_mode", action="store_true", help="Separate all .md files in directory into multiple .xlsx files")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
    return parser


def _build_convert_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MAMOW: Convert between Gherkin, Markdown, and Excel",
        add_help=False,
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input file")
    parser.add_argument("-f", "--format", required=True, choices=["md", "gherkin", "feature", "excel"],
                        help="Target output format")
    parser.add_argument("-o", "--output", default=None, help="Path to output file")
    return parser


def main():
    if len(sys.argv) == 1:
        print_banner()
        print_main_help()
        sys.exit(0)

    if "-h" in sys.argv or "--help" in sys.argv:
        if len(sys.argv) >= 2 and sys.argv[1] == "convert":
            print_banner()
            print_convert_help()
        else:
            print_banner()
            print_md_to_excel_help()
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == "convert":
        convert_parser = _build_convert_parser()
        args = convert_parser.parse_args(sys.argv[2:])
        run_convert(args)
        return

    legacy_parser = _build_legacy_parser()
    args = legacy_parser.parse_args()
    
    if args.merge and args.single_mode:
        console.print(Panel(
            "[error]Cannot use [primary]--merge[/primary] and [primary]--single[/primary] together.[/error]",
            title="[error]Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)
        
    config = load_config_with_migration(args.config)
    default_input_dir = getattr(config, 'default_input_dir', 'samples/input')
    default_output_dir = getattr(config, 'default_output_dir', 'samples/output')
    
    input_path = Path(args.input)
    if not input_path.exists():
        fallback_path = Path(default_input_dir) / args.input
        if fallback_path.exists():
            input_path = fallback_path
        else:
            console.print(Panel(
                f"[error]Input path '[path]{args.input}[/path]' does not exist.[/error]",
                title="[error]Error[/error]",
                border_style="error",
                expand=False
            ))
            sys.exit(1)
            
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == ".xlsx" and args.output == output_path.name:
            output_path = Path(default_output_dir) / args.output
    else:
        output_path = Path(default_output_dir)

    # ── Auto-create result_<input_folder> subfolder for directory inputs ──
    if input_path.is_dir():
        if output_path.suffix == ".xlsx":
            # --merge with explicit .xlsx path → insert result_ into parent dir
            base_dir = output_path.parent
            result_dir = create_result_subfolder(input_path, base_dir)
            output_path = result_dir / output_path.name
        else:
            output_path = create_result_subfolder(input_path, output_path)

    console.print(Rule(f"[primary]MAMOW[/primary] - [dim]Processing[/dim]", style="primary"))
    console.print(f"  [info]Input:[/info]  [path]{input_path}[/path]")
    console.print(f"  [info]Output:[/info] [path]{output_path}[/path]")
    if args.merge:
        console.print(f"  [info]Mode:[/info]   [accent]Merge[/accent] (combine all .md into single .xlsx)")
    elif args.single_mode:
        console.print(f"  [info]Mode:[/info]   [accent]Single[/accent] (export each .md to separate .xlsx)")
    else:
        console.print(f"  [info]Mode:[/info]   [accent]Batch[/accent] (process each .md individually)")
    console.print()
    
    if input_path.is_file():
        if args.merge or args.single_mode:
            console.print(Panel(
                "[warning]Warning:[/warning] [primary]--merge[/primary] and [primary]--single[/primary] are ignored when input is a single file.[/warning]",
                title="[warning]Note[/warning]",
                border_style="warning",
                expand=False
            ))
            
        if output_path.suffix == ".xlsx":
            out_dir = output_path.parent
            out_name = output_path.name
        else:
            out_dir = output_path
            out_name = input_path.stem + ".xlsx"
        
        process_file(input_path, out_dir, out_name)
        
    elif input_path.is_dir():
        md_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix == '.md']
        if not md_files:
            console.print(Panel(
                f"[warning]No .md files found in directory '[path]{input_path}[/path]'.[/warning]",
                title="[warning]Warning[/warning]",
                border_style="warning",
                expand=False
            ))
            sys.exit(0)
            
        if args.merge:
            if args.output and output_path.suffix != ".xlsx":
                console.print(Panel(
                    "[error]Output path must be a .xlsx file when using [primary]--merge[/primary] with a directory.[/error]",
                    title="[error]Error[/error]",
                    border_style="error",
                    expand=False
                ))
                sys.exit(1)
                
            if output_path.suffix == ".xlsx":
                out_dir = output_path.parent
                out_name = output_path.stem + "_merge.xlsx"
            else:
                out_dir = output_path
                out_name = input_path.name + "_merge.xlsx"
                
            console.print(f"[info]Found [primary]{len(md_files)}[/primary] Markdown files. Merging into [path]{out_dir / out_name}[/path]...[/info]")
            console.print()
            
            modules_with_names = []
            failed = 0
            with Progress(
                SpinnerColumn(spinner_name="dots12", style="primary"),
                TextColumn("[primary]Parsing[/primary] [path]{task.description}[/path]"),
                BarColumn(bar_width=None, style="dim", complete_style="primary"),
                TaskProgressColumn(style="info"),
                console=console,
            ) as progress:
                task = progress.add_task("files", total=len(md_files))
                for md_file in md_files:
                    try:
                        md_parser = MarkdownParser(md_file)
                        module = md_parser.parse()
                        modules_with_names.append((module, md_file.stem))
                    except Exception as e:
                        console.print(f"  [error]✗[/error] [error]Error parsing {md_file}: {e}[/error]")
                        failed += 1
                    progress.advance(task)
            
            if modules_with_names:
                with Progress(
                    SpinnerColumn(spinner_name="dots12", style="success"),
                    TextColumn("[success]Exporting[/success] [path]{task.description}[/path]"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task("export", total=None)
                    exporter = ExcelExporter(out_dir)
                    exporter.export_batch(modules_with_names, out_name)
                
                console.print(Panel(
                    f"[success]Successfully merged [primary]{len(modules_with_names)}[/primary] files[/success]"
                    + (f"\n[warning]{failed} file(s) failed to parse[/warning]" if failed else ""),
                    title="[success]Done[/success]",
                    border_style="success",
                    expand=False
                ))
                
        elif args.single_mode:
            if args.output and output_path.suffix == ".xlsx":
                console.print(Panel(
                    "[error]Output path must be a directory when using [primary]--single[/primary].[/error]",
                    title="[error]Error[/error]",
                    border_style="error",
                    expand=False
                ))
                sys.exit(1)
            
            out_dir = output_path
            console.print(f"[info]Found [primary]{len(md_files)}[/primary] Markdown files. Exporting separate files to [path]{out_dir}[/path]...[/info]")
            console.print()
            
            modules_with_filenames = []
            used_out_names = set()
            failed = 0
            
            with Progress(
                SpinnerColumn(spinner_name="dots12", style="primary"),
                TextColumn("[primary]Parsing[/primary] [path]{task.description}[/path]"),
                BarColumn(bar_width=None, style="dim", complete_style="primary"),
                TaskProgressColumn(style="info"),
                console=console,
            ) as progress:
                task = progress.add_task("files", total=len(md_files))
                for md_file in md_files:
                    try:
                        md_parser = MarkdownParser(md_file)
                        module = md_parser.parse()
                        
                        base_stem = md_file.stem
                        out_name = f"{base_stem}_single.xlsx"
                        counter = 1
                        
                        while (out_dir / out_name).exists() or out_name in used_out_names:
                            out_name = f"{base_stem}_single_{counter}.xlsx"
                            counter += 1
                            
                        used_out_names.add(out_name)
                        modules_with_filenames.append((module, out_name))
                    except Exception as e:
                        console.print(f"  [error]✗[/error] [error]Error parsing {md_file}: {e}[/error]")
                        failed += 1
                    progress.advance(task)
            
            if modules_with_filenames:
                with Progress(
                    SpinnerColumn(spinner_name="dots12", style="success"),
                    TextColumn("[success]Exporting[/success] [path]{task.description}[/path]"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task("export", total=None)
                    exporter = ExcelExporter(out_dir)
                    exporter.export_multiple(modules_with_filenames)
                
                console.print(Panel(
                    f"[success]Successfully exported [primary]{len(modules_with_filenames)}[/primary] files[/success]"
                    + (f"\n[warning]{failed} file(s) failed to parse[/warning]" if failed else ""),
                    title="[success]Done[/success]",
                    border_style="success",
                    expand=False
                ))
                
        else:
            if output_path.suffix == ".xlsx":
                console.print(Panel(
                    "[error]Output must be a directory when input is a directory.[/error]",
                    title="[error]Error[/error]",
                    border_style="error",
                    expand=False
                ))
                sys.exit(1)
                
            console.print(f"[info]Found [primary]{len(md_files)}[/primary] Markdown files. Processing batch...[/info]")
            console.print()
            
            for md_file in md_files:
                out_name = md_file.stem + ".xlsx"
                process_file(md_file, output_path, out_name)
    else:
        console.print(Panel(
            f"[error]Invalid input path '[path]{input_path}[/path]'.[/error]",
            title="[error]Error[/error]",
            border_style="error",
            expand=False
        ))
        sys.exit(1)

if __name__ == "__main__":
    main()
