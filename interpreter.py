import sys
from pathlib import Path
from merccompilec import compile_source, read_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py <source_file>")
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"File '{source_file}' not found.")
        sys.exit(1)

    source_code = read_file(source_file)
    # Pass the directory to handle Mercury modules
    compiled_code = compile_source(source_code, module_dir=source_file.parent)

    exec(compiled_code)

if __name__ == "__main__":
    main()
