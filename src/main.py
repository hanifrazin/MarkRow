import argparse
import sys
from pathlib import Path

# Ensure the root project directory is in sys.path so 'src.*' imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.config import ConfigManager
from src.engine.parser import MarkdownParser
from src.engine.exporter import ExcelExporter

def process_file(input_path: Path, out_dir: Path, out_name: str):
    print(f"Processing {input_path}...")
    try:
        md_parser = MarkdownParser(input_path)
        module = md_parser.parse()
        
        exporter = ExcelExporter(out_dir)
        exporter.export(module, out_name)
        print(f"  -> Exported to {out_dir / out_name}")
    except Exception as e:
        print(f"  -> Error processing {input_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="MarkRow: Parse Markdown test cases into Excel")
    parser.add_argument("-i", "--input", required=True, help="Path to input Markdown file or directory")
    parser.add_argument("-o", "--output", default=None, help="Path to output file or directory")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config.json")
    
    # New flags
    parser.add_argument("--merge", action="store_true", help="Merge all .md files in directory into 1 .xlsx file")
    parser.add_argument("--single", dest="single_mode", action="store_true", help="separate all .md files in directory into multiple .xlsx files")
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    
    if args.merge and args.single_mode:
        print("Error: Cannot use --merge and --single together.")
        sys.exit(1)
        
    config = ConfigManager.load(args.config)
    default_input_dir = getattr(config, 'default_input_dir', 'samples/input')
    default_output_dir = getattr(config, 'default_output_dir', 'samples/output')
    
    input_path = Path(args.input)
    if not input_path.exists():
        fallback_path = Path(default_input_dir) / args.input
        if fallback_path.exists():
            input_path = fallback_path
        else:
            print(f"Error: Input path '{args.input}' does not exist.")
            sys.exit(1)
            
    if args.output:
        output_path = Path(args.output)
        # If output is just a filename (no directory) and ends with .xlsx, put it in default_output_dir
        if output_path.suffix == ".xlsx" and args.output == output_path.name:
            output_path = Path(default_output_dir) / args.output
    else:
        output_path = Path(default_output_dir)
    
    if input_path.is_file():
        if args.merge or args.single_mode:
            print("Warning: --merge and --single are ignored when input is a single file.")
            
        if output_path.suffix == ".xlsx":
            out_dir = output_path.parent
            out_name = output_path.name
        else:
            out_dir = output_path
            out_name = input_path.stem + ".xlsx"
        
        process_file(input_path, out_dir, out_name)
        
    elif input_path.is_dir():
        # Get only .md files at the root of the directory (ignore subdirectories)
        md_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix == '.md']
        if not md_files:
            print(f"Warning: No .md files found in directory '{input_path}'.")
            sys.exit(0)
            
        if args.merge:
            if args.output and output_path.suffix != ".xlsx":
                print("Error: Output path must be a .xlsx file when using --merge with a directory.")
                sys.exit(1)
                
            if output_path.suffix == ".xlsx":
                out_dir = output_path.parent
                out_name = output_path.name
            else:
                out_dir = output_path
                out_name = input_path.name + ".xlsx"
                
            print(f"Found {len(md_files)} Markdown files. Merging into {out_dir / out_name}...")
            
            modules_with_names = []
            for md_file in md_files:
                try:
                    md_parser = MarkdownParser(md_file)
                    module = md_parser.parse()
                    modules_with_names.append((module, md_file.stem))
                except Exception as e:
                    print(f"  -> Error parsing {md_file}: {e}")
                    
            if modules_with_names:
                exporter = ExcelExporter(out_dir)
                exporter.export_batch(modules_with_names, out_name)
                print(f"  -> Successfully merged {len(modules_with_names)} files.")
                
        elif args.single_mode:
            if args.output and output_path.suffix == ".xlsx":
                print("Error: Output path must be a directory when using --single.")
                sys.exit(1)
                
            out_dir = output_path
            print(f"Found {len(md_files)} Markdown files. singleing into separate files in {out_dir}...")
            
            modules_with_filenames = []
            used_out_names = set()
            for md_file in md_files:
                try:
                    md_parser = MarkdownParser(md_file)
                    module = md_parser.parse()
                    
                    base_stem = md_file.stem
                    out_name = f"{base_stem}.xlsx"
                    counter = 1
                    
                    while (out_dir / out_name).exists() or out_name in used_out_names:
                        out_name = f"{base_stem}_{counter}.xlsx"
                        counter += 1
                        
                    used_out_names.add(out_name)
                    modules_with_filenames.append((module, out_name))
                except Exception as e:
                    print(f"  -> Error parsing {md_file}: {e}")
                    
            if modules_with_filenames:
                exporter = ExcelExporter(out_dir)
                exporter.export_multiple(modules_with_filenames)
                print(f"  -> Successfully exported {len(modules_with_filenames)} files.")
                
        else:
            if output_path.suffix == ".xlsx":
                print("Error: Output must be a directory when input is a directory.")
                sys.exit(1)
                
            print(f"Found {len(md_files)} Markdown files. Processing batch...")
            for md_file in md_files:
                out_name = md_file.stem + ".xlsx"
                process_file(md_file, output_path, out_name)
    else:
        print(f"Error: Invalid input path '{input_path}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
